import time
import argparse
import pandas as pd
import numpy as np
import json
from pathlib import Path
from tqdm import tqdm
from worldbuilder.utils import load_multi_yaml


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

        if k == "description":
            yield (prior_keys + ["description"], v)

        if k in IGNORED_KEYS:
            continue

        for x in world_step(d[k], prior_keys + [k]):
            yield x


IGNORED_KEYS = [
    "world_names",
    "basic_cities",
    "basic_residents",
]

CLOSEUP_KEYS = ["races", "creatures", "resident_description"]
subareas = ["races", "creatures", "landmarks", "lore", "deities", "beliefs"]
ITR = []

world = js["content"]

for k, v in world_step(world, []):
    if any([x in k for x in subareas]):
        for line in v.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line[0] not in "-+":
                continue
            line = line.strip("-+").strip()
            ITR.append((k, line))
    else:
        ITR.append((k, v))

save_dest = Path("results") / "images" / world_name.replace(" ", "_")
save_dest.mkdir(exist_ok=True, parents=True)

df = pd.DataFrame(data=ITR, columns=["key", "prompt"])
df["f_save"] = [save_dest / f"{k:06d}.png" for k in range(len(df))]


# Mark the close-ups
df["is_closeup"] = [any([x in CLOSEUP_KEYS for x in z]) for z in df["key"]]
df["negative_prompt"] = topics[args_topic]["negative_prompt"]
df["style_prompt"] = topics[args_topic]["style_prompt"]

df.loc[df.is_closeup, "style_prompt"] = (
    "closeup, " + df.loc[df.is_closeup]["style_prompt"]
)

# Save the result
f_csv = Path("results") / "images" / (world_name + ".csv")
df.to_csv(f_csv, index=False)

# Only generate the new images
idx = np.array([x.exists() for x in df.f_save])
df = df[~idx]

# Force the main topic into the images
IGNORE_FORCE_PROMPT = ["creatures"]
idx = [not any([x in IGNORE_FORCE_PROMPT for x in z]) for z in df["key"]]

main_text = main_topic.replace("(", " ").replace(")", " ")
main_text = main_text.replace("[", " ").replace("]", " ")
df.loc[idx, "prompt"] = df.loc[idx, "prompt"] + f" ({main_text} : 0.90)"


# Exit peacefully if no work is needed
if not len(df):
    print("All done!")
    exit(0)


from selenium import webdriver  # noqa: E402
from selenium.webdriver.support.ui import WebDriverWait  # noqa: E402
from selenium.webdriver.common.by import By  # noqa: E402
from pathlib import Path  # noqa: E402

url = "http://127.0.0.1:7860/"

# create a new instance of the Firefox driver
driver = webdriver.Firefox()

# navigate to the webpage that contains the form
driver.get(url)
WebDriverWait(driver, 5)


def generate_image(ptext, ntext, stext):
    elements = driver.find_elements(By.XPATH, "//*[@placeholder]")

    # First two elements are what we are looking for
    prompt_textbox = elements[0]
    neg_prompt_textbox = elements[1]

    prompt_textbox.clear()
    prompt_textbox.send_keys(stext.strip() + "\n")
    prompt_textbox.send_keys(ptext.strip())

    neg_prompt_textbox.clear()
    neg_prompt_textbox.send_keys(ntext.strip())

    WebDriverWait(driver, 1)
    time.sleep(1)

    # Clear the directory
    save_dest = (
        Path("SD_image_gen_app") / "stable-diffusion-webui" / "log" / "images"
    )
    for f in save_dest.glob("*.png"):
        if f.is_file():
            f.unlink()

    # Generate the image
    ID = driver.find_element(By.ID, "txt2img_generate_box")
    inputbox = ID.find_elements(By.TAG_NAME, "button")[2]
    inputbox.click()
    WebDriverWait(driver, 12)
    time.sleep(10)

    # Save the image
    ID = driver.find_element(By.ID, "save_txt2img")
    ID.click()
    WebDriverWait(driver, 1)
    time.sleep(1)

    # Return a Pathlib object of the new image
    F_PNG = save_dest.glob("*.png")
    F_PNG = sorted(F_PNG, key=lambda x: Path(x).stat().st_mtime, reverse=True)
    f_png = F_PNG[0]
    return f_png


neg_text = topics[args_topic]["negative_prompt"]

for f_save, prompt, stext in tqdm(
    zip(df.f_save, df.prompt, df.style_prompt), total=len(df)
):
    f_png = generate_image(prompt, neg_text, stext)
    f_png.rename(f_save)
    print(f_save)

# Finish up and shutdown
driver.close()
driver.quit()
