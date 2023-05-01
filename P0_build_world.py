import json
import argparse
import diskcache as dc
from wasabi import msg as MSG
from pathlib import Path
from slugify import slugify
from worldbuilder import WorldBuilder, Cached_ChatGPT
from worldbuilder.utils import load_multi_yaml, load_single_yaml

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
NUM_QUERY_THREADS = 1

f_yaml_templates = "templates.yaml"
topics = load_multi_yaml(f_yaml_templates)

try:
    main_topic = topics[args_topic]["prompt"]
except KeyError as EX:
    print(f"Topic {args_topic} not found in {f_yaml_templates}")
    raise EX

#########################################################################

# Load a cache, a GPT query, and world builder
cache = dc.Cache(f"cache/{slugify(main_topic)[:230]}/worldbuilding")
GPT = Cached_ChatGPT(cache, max_tokens)
WORLD = WorldBuilder(GPT, main_topic=main_topic)

f_yaml_schema = "schema/world.yaml"
schema = load_multi_yaml(f_yaml_schema)

f_yaml_meta = "schema/meta.yaml"
meta = load_single_yaml(f_yaml_meta)

#########################################################################

# Query GPT to get a list of names
names = WORLD(schema["world_names"], is_list=False)

# Ask the user for a specific name or choose one from the cmd args
prefixed_name = topics[args_topic]["world_name"]
if prefixed_name is not None and prefixed_name.strip():
    world_name = prefixed_name

else:
    print(f"Edit the yaml file {f_yaml_templates} to fix the name")
    print("Choose a world name:")
    print(names)
    # world_selection_index = int(input("> "))
    # world_name = names[world_selection_index]
    exit(2)

MSG.info(f"Building the world {world_name}")
WORLD.build_args["world_name"] = world_name

######################################################################

print(WORLD(schema["world_description"], is_list=False))
print(WORLD(schema["races"]))
print(WORLD(schema["creatures"]))
print(WORLD(schema["basic_cities"]))
print(WORLD(schema["deities"]))
print(WORLD(schema["landmarks"]))
print(WORLD(schema["beliefs"]))
print(WORLD(schema["relics"]))

############################################################################
# Save the output to the "basic" folder for the next round

meta["main_topic"] = main_topic
meta["world_name"] = world_name

js = {
    "content": WORLD.content,
    "prompts": WORLD.prompts,
    "short_prompts": WORLD.short_prompts,
    "meta": meta,
}

save_dest = Path("results") / "worldbuilding"
save_dest.mkdir(exist_ok=True, parents=True)

f_save = save_dest / f"{args_topic}.json"

with open(f_save, "w") as FOUT:
    FOUT.write(json.dumps(js, indent=2))

MSG.info(f"Saved to {f_save}")
MSG.info(f"Make sure to update {f_yaml_templates} with world_name")
