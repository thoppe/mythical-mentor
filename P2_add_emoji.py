from dspipe import Pipe
import copy
import json
import argparse
import diskcache as dc
from wasabi import msg as MSG
from pathlib import Path
from slugify import slugify
from worldbuilder import WorldBuilder, Cached_ChatGPT
from worldbuilder.utils import load_multi_yaml

parser = argparse.ArgumentParser(
    description="Generate an world from a base prompt."
)
parser.add_argument("--topic", type=str, help="Base prompt")

parser.add_argument(
    "--MAX_TOKENS",
    type=int,
    default=1000,
    help="Limit on number of tokens to use",
)

# Parse the arguments
args = parser.parse_args()

args_topic = args.topic
max_tokens = args.MAX_TOKENS
NUM_QUERY_THREADS = 8

f_yaml_templates = "templates.yaml"
topics = load_multi_yaml(f_yaml_templates)

try:
    main_topic = topics[args_topic]["prompt"]
except KeyError as EX:
    print(f"Topic {args_topic} not found in {f_yaml_templates}")
    raise EX

#########################################################################

f_world = Path("results") / "worldbuilding" / f"{args_topic}.json"

with open(f_world) as FIN:
    js = json.load(FIN)

world_name = js["meta"]["world_name"]

#########################################################################

# Load a cache, a GPT query, and world builder
cache = dc.Cache(f"cache/{slugify(main_topic)[:230]}/emoji")
GPT = Cached_ChatGPT(cache, max_tokens)
WORLD = WorldBuilder(GPT, main_topic=main_topic)

f_yaml_schema = "schema/world.yaml"
schema = load_multi_yaml(f_yaml_schema)

#########################################################################


def world_step(d, prior_keys=None):

    if prior_keys is None:
        prior_keys = []

    if isinstance(d, str):
        yield prior_keys, d
        return

    for k, v in d.items():
        for x in world_step(d[k], prior_keys + [k]):
            yield x


def process_emoji(item, force=False):
    key, value, WORLD = item
    SUBSET = copy.deepcopy(WORLD)
    SUBSET.build_args["topic"] = value
    emoji = SUBSET(schema["emoji"], is_list=False, force=force)
    emoji = emoji.split("\n")[0].strip()
    if not len(emoji) or (0 <= ord(emoji[0]) <= 255):
        print(emoji)
        return process_emoji(item, force=True)

    print(key, emoji)
    return key, emoji


ITR = [(k, v, WORLD) for k, v in world_step(js["content"])]
js["emoji"] = Pipe(ITR)(process_emoji, NUM_QUERY_THREADS)

with open(f_world, "w") as FOUT:
    FOUT.write(json.dumps(js, indent=2))

MSG.info(f"Saved to {f_world}")
