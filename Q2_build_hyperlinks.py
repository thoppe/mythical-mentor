import argparse
import json
from pathlib import Path
from worldbuilder.utils import load_multi_yaml, recover_bulleted_list
from wasabi import msg as MSG

parser = argparse.ArgumentParser(
    description="Generate an world from a base idea."
)
parser.add_argument("--topic", type=str, help="Base idea")

args = parser.parse_args()
args_topic = args.topic

f_yaml_templates = "templates.yaml"
topics = load_multi_yaml(f_yaml_templates)
main_topic = topics[args_topic]["prompt"]

f_world = Path("results") / "worldbuilding" / f"{args_topic}.json"

with open(f_world) as FIN:
    js = json.load(FIN)
    world_name = js["meta"]["world_name"]


def world_step(d, prior_keys=None):

    if prior_keys is None:
        prior_keys = []

    if isinstance(d, str):
        yield prior_keys, d
        return

    for k, v in d.items():
        for x in world_step(d[k], prior_keys + [k]):
            yield x


LIST_CONTENT = ["races", "creatures", "deities", "landmarks", "beliefs"]
world = js["content"]
linkables = {}

# Step through the world and look for potential hyperlinks
for k, v in world_step(world, []):
    if k[-1] in LIST_CONTENT:
        for item in recover_bulleted_list(v):
            name = item.split(":")[0].strip()
            linkables[name] = k
    if len(k) > 1 and k[-2] == "residents":
        name = k[-1].split(":")[0].strip()
        linkables[name] = k

data = {}

for k, v in world_step(world, []):
    hi_name = " ".join(k)
    data[hi_name] = []

    for lk in linkables.keys():
        if lk in v:
            idx = v.index(lk)
            if k == linkables[lk]:
                continue

            data[hi_name].append((linkables[lk], idx))

js = json.dumps(data, indent=2)

save_dest = Path("results") / "images" / world_name
save_dest.mkdir(exist_ok=True, parents=True)

# Save the result
f_json = Path("results") / "images" / (world_name + "_links" + ".json")
with open(f_json, "w") as FOUT:
    FOUT.write(js)

MSG.info(f"Saved link results to {f_json}")
