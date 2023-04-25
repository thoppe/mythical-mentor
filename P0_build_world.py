import json
import argparse
import diskcache as dc
from utils import query
from wasabi import msg as MSG
from pathlib import Path
from slugify import slugify


parser = argparse.ArgumentParser(
    description="Generate an world from a base idea."
)
parser.add_argument("--topic", type=str, help="Base idea")

parser.add_argument(
    "--MAX_TOKENS",
    type=int,
    default=1000,
    help="Limit on number of tokens to use",
)

# Parse the arguments
args = parser.parse_args()

main_topic = args.topic
max_tokens = args.MAX_TOKENS
NUM_QUERY_THREADS = 1

cache = dc.Cache(f"cache/{slugify(main_topic)[:230]}/worldbuilding")


@cache.memoize()
def ASK(messages, n=1):
    js = query(messages, max_tokens=max_tokens, n=n)
    token_cost = js["usage"]["total_tokens"]
    MSG.warn(f"'{main_topic}' TOKENS USED {token_cost}")
    return js


def SIMPLE_ASK(q, n=1):
    messages = [{"role": "user", "content": q}]
    return ASK(messages, n=n)


def recover_content(response):
    return response["choices"][0]["message"]["content"]


def recover_bulleted_list(content):
    # Only pulls out the bulleted lists
    items = [x for x in content.split("\n") if x and x[0] in ["-", "+"]]
    items = [x.strip(" -").strip(" -") for x in items]
    return items


Q = {}

# Start by defining some names for our world
Q[
    "world_names"
] = f"""You are an expert worldbuilder, and are designing a {main_topic}. Enumerate names for this world in a bulleted list. Do not use any known names. Do not include a description."""
names = recover_bulleted_list(recover_content(SIMPLE_ASK(Q["world_names"])))

# Choose the last name in the list
world = {"name": names[-1]}
MSG.info(f"Building the world {world['name']}")

# Describe the world
Q[
    "description"
] = f"""You are an expert worldbuilder, and are designing a {main_topic}. The name of the world is {world['name']}. Describe this world for me. Be extremely high level and be specific technology, magic, and culture that are available."""
world["description"] = recover_content(SIMPLE_ASK(Q["description"]))
print(world["description"])

# Describe some of the races
Q[
    "races"
] = f"""List some of the races in the world of {world['name']} in a bulleted list. Do not use any previously known names for the races. Describe their interaction with the technology and culture of {world['name']}. Return the results in a bulleted list only."""
messages = [
    {"role": "user", "content": Q["description"]},
    {"role": "assistant", "content": world["description"]},
    {"role": "user", "content": Q["races"]},
]
world["races"] = recover_content(ASK(messages))
print(world["races"])

# Describe some of the creatures and how they interact with the races
Q[
    "creatures"
] = f"""List some of the creatures that inhabit the world of {world['name']} in a bulleted list. Do not use any previously known names for the creatures. Do not use any names found in books or games. Describe their interaction with the known races {world['name']}. Return the results in a bulleted list only."""
messages = [
    {"role": "user", "content": Q["description"]},
    {"role": "assistant", "content": world["description"]},
    {"role": "user", "content": Q["races"]},
    {"role": "assistant", "content": world["races"]},
    {"role": "user", "content": Q["creatures"]},
]
world["creatures"] = recover_content(ASK(messages))
print(world["creatures"])

# Describe some of the major cities and what races live there
Q[
    "cities"
] = f"""List some of the major cities, towns, or villages that are in the world of {world['name']} in a bulleted list. Do not use any previously known names. Do not use any names found in books or games. Describe what races live in them. Return the results in a bulleted list only."""
messages = [
    {"role": "user", "content": Q["description"]},
    {"role": "assistant", "content": world["description"]},
    {"role": "user", "content": Q["races"]},
    {"role": "assistant", "content": world["races"]},
    {"role": "user", "content": Q["cities"]},
]
world["cities"] = recover_content(ASK(messages))
print(recover_bulleted_list(world["cities"]))

# Describe the languages of each race
Q[
    "languages"
] = """For each of the races, describe their language in a bulleted list. Do not use any previously known names. Return the results in a bulleted list only."""
messages = [
    {"role": "user", "content": Q["description"]},
    {"role": "assistant", "content": world["description"]},
    {"role": "user", "content": Q["races"]},
    {"role": "assistant", "content": world["races"]},
    {"role": "user", "content": Q["languages"]},
]
world["languages"] = recover_content(ASK(messages))
print(recover_bulleted_list(world["languages"]))


# Describe some of the major landmarks or ruins
Q[
    "landmarks"
] = f"""List some of the major landmarks or ruins in the world of {world['name']} in a bulleted list. Do not include places where any of the races live like towns or villages. Do not use any names found in books or games. Make the names of the places evocative. Let the places be named in the tongue and language of the known races. Describe the history of the place and how the races interact with it. Return the results in a bulleted list only."""
messages = [
    {"role": "user", "content": Q["description"]},
    {"role": "assistant", "content": world["description"]},
    {"role": "user", "content": Q["races"]},
    {"role": "assistant", "content": world["races"]},
    {"role": "user", "content": Q["languages"]},
    {"role": "assistant", "content": world["languages"]},
    {"role": "user", "content": Q["landmarks"]},
]
world["landmarks"] = recover_content(ASK(messages))

js = {
    "world": world,
    "prompts": Q,
}

save_dest = Path("results") / "basic" / slugify(main_topic)[:230]
save_dest.mkdir(exist_ok=True, parents=True)

f_save = save_dest / f"{world['name']}.json"

with open(f_save, "w") as FOUT:
    FOUT.write(json.dumps(js, indent=2))

MSG.info(f"Saved to {f_save}")
