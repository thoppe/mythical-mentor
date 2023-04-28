import json
from dspipe import Pipe
import argparse
import diskcache as dc
from utils import recover_bulleted_list, Cached_ChatGPT
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
    default=1200,
    help="Limit on number of tokens to use",
)

# Parse the arguments
args = parser.parse_args()

main_topic = args.topic
max_tokens = args.MAX_TOKENS
NUM_QUERY_THREADS = 4


def get_inhabitants(item):
    resident, basic_city_desc, world, city, Q, QS = item

    city_name = basic_city_desc.split(":")[0]

    q = f"""Describe in great visual detail this character in {city_name}. {resident}"""

    messages = [
        base_q0,
        base_q1,
        {"role": "user", "content": QS["races"]},
        {"role": "assistant", "content": world["races"]},
        {"role": "user", "content": Q["description"]},
        {"role": "assistant", "content": city["description"]},
        {"role": "user", "content": Q["residents"]},
        {"role": "assistant", "content": city["residents"]},
        {"role": "user", "content": Q["lore"]},
        {"role": "assistant", "content": city["lore"]},
        {"role": "user", "content": q},
    ]
    x = GPT.ASK(messages, expect_list=False)
    return x, resident, q


def get_city_detail(item):
    basic_city_desc, world, QS = item

    Q = {}
    city = {"basic_city_desc": basic_city_desc}

    Q[
        "description"
    ] = f"""{main_topic}. Describe in great detail {basic_city_desc} Include the history, arts, culture, major events. Do not list any specific residents."""
    messages = [
        {"role": "user", "content": QS["description"]},
        {"role": "assistant", "content": world["description"]},
        {"role": "user", "content": QS["races"]},
        {"role": "assistant", "content": world["races"]},
        {"role": "user", "content": Q["description"]},
    ]

    # Shorten the description
    Q[
        "description"
    ] = "Describe the city. Include the history, arts, culture, major events."

    city["description"] = GPT.ASK(messages, expect_list=False)
    print(city["description"])

    Q[
        "residents"
    ] = f"""{main_topic}. Using a bulleted list denoted by dashes, help imagine some of the famous residents and characters and what makes each of them unique in {basic_city_desc} Give them each a character name, their race, and a backstory."""
    messages = [
        base_q0,
        base_q1,
        {"role": "user", "content": QS["races"]},
        {"role": "assistant", "content": world["races"]},
        {"role": "user", "content": Q["description"]},
        {"role": "assistant", "content": city["description"]},
        {"role": "user", "content": Q["residents"]},
    ]
    # Shorten the description
    Q["residents"] = "Describe some of the famous residents and characters."

    city["residents"] = GPT.ASK(messages, expect_list=True)
    print(city["residents"])

    Q[
        "lore"
    ] = f"""{main_topic}. Using a bulleted list denoted by dashes, help imagine some of the major historical events and drama in {basic_city_desc} Use the famous residents and characters in each item."""

    messages = [
        {"role": "user", "content": QS["races"]},
        {"role": "assistant", "content": world["races"]},
        {"role": "user", "content": Q["description"]},
        {"role": "assistant", "content": city["description"]},
        {"role": "user", "content": Q["residents"]},
        {"role": "assistant", "content": city["residents"]},
        {"role": "user", "content": Q["lore"]},
    ]

    city["lore"] = GPT.ASK(messages, expect_list=True)
    print(city["lore"])

    city["inhabitants"] = {}
    Q["inhabitants"] = {}

    ITR = [
        (resident, basic_city_desc, world, city, Q, QS)
        for resident in recover_bulleted_list(city["residents"])
    ]

    for x, resident, qx in Pipe(ITR)(get_inhabitants, NUM_QUERY_THREADS):

        resident_name = resident.split(",")[0].split(":")[0]
        city["inhabitants"][resident_name] = x
        Q["inhabitants"][resident_name] = qx

    return basic_city_desc, Q, city


# Load the prior results, load only the first world in the list

load_dest = Path("results") / "basic" / slugify(main_topic)[:230]
f_world = list(load_dest.glob("*.json"))[0]

with open(f_world) as FIN:
    js = json.load(FIN)
    world = js["world"]
    # QW = js["prompts"]
    QS = js["short_prompts"]


base_q0 = {"role": "user", "content": QS["description"]}
base_q1 = {"role": "assistant", "content": world["description"]}

cache = dc.Cache(
    f"cache/{slugify(main_topic)[:230]}/worldbuilding/{world['name']}"
)
GPT = Cached_ChatGPT(cache, max_tokens)

ITR = [
    (basic_city_desc, world, QS)
    for basic_city_desc in recover_bulleted_list(world["cities"])
]

world["city_details"] = {}
QS["city_details"] = {}

for basic_city_desc, city_Q, city in Pipe(ITR)(
    get_city_detail,
    NUM_QUERY_THREADS,
):

    city_name = basic_city_desc.split(":")[0]

    world["city_details"][basic_city_desc] = city
    QS["city_details"][basic_city_desc] = city_Q


# Remove the basic city details
del world["cities"]
world["cities"] = world["city_details"]
del world["city_details"]


js = {
    "world": world,
    "prompts": QS,
    "meta": js["meta"],
}

save_dest = Path("results") / "advanced" / slugify(main_topic)[:230]
save_dest.mkdir(exist_ok=True, parents=True)

f_save = save_dest / f"{world['name']}.json"

with open(f_save, "w") as FOUT:
    FOUT.write(json.dumps(js, indent=2))

MSG.info(f"Saved to {f_save}")
