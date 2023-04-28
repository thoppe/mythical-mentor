from .utils import recover_bulleted_list


class WorldBuilder:
    def __init__(self, GPT, **kwargs):
        self.build_args = kwargs
        self.GPT = GPT

        self.world = {}
        self.prompts = {}
        self.short_prompts = {}

    def build_message_chain(self, q, prompt):
        messages = []
        for k in q["messages"]:
            messages.append({"role": "user", "content": self.short_prompts[k]})
            messages.append({"role": "assistant", "content": self.world[k]})

        messages.append({"role": "user", "content": prompt})
        return messages

    def __call__(self, q, is_list=True):

        prompt = q["prompt"].format(**self.build_args)
        short_prompt = q["short_prompt"].format(**self.build_args)

        name = q["key"]
        self.prompts[name] = prompt
        self.short_prompts[name] = short_prompt

        messages = self.build_message_chain(q, prompt)
        result = self.GPT.ASK(messages)

        self.world[name] = result

        if is_list:
            result = recover_bulleted_list(result)

        return result