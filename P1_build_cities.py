import json
import yaml
from dspipe import Pipe
import argparse
import diskcache as dc
from wasabi import msg as MSG
from pathlib import Path
from slugify import slugify
import copy
from worldbuilder import WorldBuilder, Cached_ChatGPT

parser = argparse.ArgumentParser(
    description="Generate an world from a base idea."
)
parser.add_argument("--topic", type=str, help="Base idea")

parser.add_argument(
    "--MAX_TOKENS",
    type=int,
    default=1200,
    help="Limit on number of tokens to use",
)

# Parse the arguments
args = parser.parse_args()

main_topic = args.topic
max_tokens = args.MAX_TOKENS
NUM_QUERY_THREADS = 4

#########################################################################

load_dest = Path("results") / "basic" / slugify(main_topic)[:230]

# Load only the first world
f_world = list(load_dest.glob("*.json"))[0]

with open(f_world) as FIN:
    js = json.load(FIN)
    world_name = js["meta"]["world_name"]

#########################################################################

# Load a cache, a GPT query, and world builder
cache = dc.Cache(
    f"cache/{slugify(main_topic)[:230]}/worldbuilding/{world_name}"
)
GPT = Cached_ChatGPT(cache, max_tokens)

f_yaml_schema = "schema/cities.yaml"
stream = open(f_yaml_schema, "r")
schema = {}
for item in yaml.load_all(stream, yaml.FullLoader):
    schema[item["key"]] = item

#######################################################################


def process_resident(item):
    CITY, basic_resident_desc = item
    RESIDENT = copy.deepcopy(CITY)
    resident_name = basic_resident_desc.split(":")[0]
    RESIDENT.build_args["resident_name"] = resident_name
    RESIDENT.build_args["basic_resident_desc"] = basic_resident_desc

    resident = RESIDENT(schema["residents"], is_list=False)
    return resident, resident_name


WORLD = WorldBuilder(GPT, main_topic=main_topic, world_name=world_name)
WORLD.prompts = js["prompts"]
WORLD.short_prompts = js["short_prompts"]
WORLD.content = js["content"]

WORLD.content["cities"] = {}

for basic_city_desc in WORLD.get("basic_cities"):
    CITY = copy.deepcopy(WORLD)

    city_name = basic_city_desc.split(":")[0]
    CITY.build_args["basic_city_desc"] = basic_city_desc
    CITY.build_args["city_name"] = city_name

    print(CITY(schema["city_description"], is_list=False))
    CITY(schema["basic_residents"])
    CITY(schema["lore"])

    CITY.content["residents"] = {}

    ITR = [(CITY, x) for x in CITY.get("basic_residents")]
    for item in Pipe(ITR)(process_resident, NUM_QUERY_THREADS):
        resident, resident_name = item
        CITY.content["residents"][resident_name] = resident
        print(resident)

    WORLD.content["cities"][city_name] = CITY.content

js = {
    "content": WORLD.content,
    "prompts": WORLD.prompts,
    "short_prompts": WORLD.short_prompts,
    "meta": js["meta"],
}

#######################################################################

save_dest = Path("results") / "advanced" / slugify(main_topic)[:230]
save_dest.mkdir(exist_ok=True, parents=True)

f_save = save_dest / f"{world_name}.json"

with open(f_save, "w") as FOUT:
    FOUT.write(json.dumps(js, indent=2))

MSG.info(f"Saved to {f_save}")
