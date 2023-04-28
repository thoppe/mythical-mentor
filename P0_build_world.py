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

f_yaml_schema = "schema/world.yaml"
stream = open(f_yaml_schema, "r")
SCHEMA = {}
for item in yaml.load_all(stream, yaml.FullLoader):
    SCHEMA[item["key"]] = item

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
BUILDER = WorldBuilder(GPT, main_topic=main_topic)

#########################################################################

# Query GPT to get a list of names
names = BUILDER(SCHEMA["world_names"])

# Ask the user for a specific name or choose one from the cmd args
if world_selection_index is None:
    print("Choose a world name:")
    for i, option in enumerate(names):
        print(f"{i}. {option}")
    world_selection_index = int(input("> "))

world_name = names[world_selection_index]
MSG.info(f"Building the world {world_name}")

BUILDER.build_args["world_name"] = world_name

######################################################################

print(BUILDER(SCHEMA["description"], is_list=False))
print(BUILDER(SCHEMA["races"]))
print(BUILDER(SCHEMA["creatures"]))
print(BUILDER(SCHEMA["cities"]))
print(BUILDER(SCHEMA["deities"]))
print(BUILDER(SCHEMA["landmarks"]))
print(BUILDER(SCHEMA["beliefs"]))

############################################################################
# Save the output to the "basic" folder for the next round

js = {
    "world": BUILDER.world,
    "prompts": BUILDER.prompts,
    "short_prompts": BUILDER.short_prompts,
    "meta": {
        "mythical_mentor_schema_version": mythical_mentor_schema_version,
        "main_topic": main_topic,
    },
}

save_dest = Path("results") / "basic" / slugify(main_topic)[:230]
save_dest.mkdir(exist_ok=True, parents=True)

f_save = save_dest / f"{world_name}.json"

with open(f_save, "w") as FOUT:
    FOUT.write(json.dumps(js, indent=2))

MSG.info(f"Saved to {f_save}")
