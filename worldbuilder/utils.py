import requests
from wasabi import msg as MSG
import yaml

requests.adapters.DEFAULT_RETRIES = 4

f_API_key = "API_KEY.txt"

with open(f_API_key) as FIN:
    API_KEY = FIN.read().strip()


def query(messages, temperature=0.7, max_tokens=200, n=1):

    query_url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-type": "application/json",
    }
    base_params = {
        "model": "gpt-3.5-turbo",
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": messages,
        "n": n,
    }

    params = base_params.copy()
    r = requests.post(query_url, headers=headers, json=params)

    if not r.ok:
        print(r.status_code, r.content)
        exit()

    result = r.json()

    return result


def recover_content(response):
    content = response["choices"][0]["message"]["content"]
    return content


def recover_bulleted_list(content):
    # Only pulls out the bulleted lists
    items = [x for x in content.split("\n") if x and x[0] in ["-", "+"]]
    items = [x.strip(" -").strip(" -") for x in items]
    return items


class Cached_ChatGPT:
    def __init__(self, cache, max_tokens):
        self.cache = cache
        self.max_tokens = max_tokens

    def ASK(self, messages, is_list=True, force=False, recover_con=True):

        if messages in self.cache and not force:
            if recover_con:
                return recover_content(self.cache[messages])
            else:
                return self.cache[messages]

        MSG.warn(messages[-1]["content"])

        js = query(messages, max_tokens=self.max_tokens, n=1)
        token_cost = js["usage"]["total_tokens"]
        MSG.fail(f"TOKENS USED {token_cost}")

        if is_list:
            content = recover_content(js)
            try:
                assert len(recover_bulleted_list(content)) > 1
            except Exception as EX:
                print("FAILED NOT BULLETED", EX, content)
                return self.ASK(
                    messages,
                    is_list=is_list,
                    force=force,
                )
                exit(2)

            for row in recover_bulleted_list(recover_content(js)):
                if len(row) < 100:
                    return self.ASK(
                        messages,
                        is_list=is_list,
                        force=force,
                    )

        # Cache the result
        self.cache[messages] = js

        if recover_con:
            return recover_content(self.cache[messages])
        else:
            return self.cache[messages]

    def SIMPLE_ASK(self, q):
        messages = [{"role": "user", "content": q}]
        return self.ASK(messages)


f_yaml_schema = "schema/world.yaml"


def load_multi_yaml(f_yaml):
    stream = open(f_yaml, "r")
    data = {}
    for item in yaml.load_all(stream, yaml.FullLoader):
        data[item["key"]] = item
    return data


def load_single_yaml(f_yaml):
    with open(f_yaml, "r") as FIN:
        return yaml.load(FIN, Loader=yaml.FullLoader)
