import yaml
import json
import argparse
import diskcache as dc
from wasabi import msg as MSG
from pathlib import Path
from slugify import slugify
from worldbuilder import WorldBuilder, Cached_ChatGPT

mythical_mentor_schema_version = 2.0

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

parser.add_argument(
    "--world_selection_index",
    type=int,
    default=None,
    help="Pre-select the world to use",
)

# Parse the arguments
args = parser.parse_args()

main_topic = args.topic
max_tokens = args.MAX_TOKENS
world_selection_index = args.world_selection_index
NUM_QUERY_THREADS = 1

#########################################################################

# Load a cache, a GPT query, and world builder
cache = dc.Cache(f"cache/{slugify(main_topic)[:230]}/worldbuilding")
GPT = Cached_ChatGPT(cache, max_tokens)
WORLD = WorldBuilder(GPT, main_topic=main_topic)

f_yaml_schema = "schema/world.yaml"
stream = open(f_yaml_schema, "r")
schema = {}
for item in yaml.load_all(stream, yaml.FullLoader):
    schema[item["key"]] = item

f_yaml_meta = "schema/meta.yaml"
with open(f_yaml_meta, "r") as file:
    meta = yaml.load(file, Loader=yaml.FullLoader)

#########################################################################

# Query GPT to get a list of names
names = WORLD(schema["world_names"])

# Ask the user for a specific name or choose one from the cmd args
if world_selection_index is None:
    print("Choose a world name:")
    for i, option in enumerate(names):
        print(f"{i}. {option}")
    world_selection_index = int(input("> "))

world_name = names[world_selection_index]
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

save_dest = Path("results") / "basic" / slugify(main_topic)[:230]
save_dest.mkdir(exist_ok=True, parents=True)

f_save = save_dest / f"{world_name}.json"

with open(f_save, "w") as FOUT:
    FOUT.write(json.dumps(js, indent=2))

MSG.info(f"Saved to {f_save}")
