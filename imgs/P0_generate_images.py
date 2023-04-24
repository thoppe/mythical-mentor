import time
import pandas as pd
import numpy as np
import json
from pathlib import Path
from tqdm import tqdm

f_json = "../results/advanced/high-fantasy-world-recovering-after-the-great-sundering/Solandria.json"
style_text = """Antoine Blanchard, (masterpiece:1.1), (best quality:1.1), dreamlikeart, absurdres, highres, photorealistic, real, contrast lighting, by Anders Zorn"""

f_json = "../results/advanced/magical-world-set-on-an-archipelago-with-perpetual-auroras-geopolitics-magic-weather-fanatical-religious-sects-freeholders-and-gangs/Twilight Territory.json"
style_text = """painterly style, flat colours, illustration, bright and colourful, high contrast, Mythology, cinematic, detailed, atmospheric, 8k, corona render."""

f_json = "../results/advanced/steampunk-world-that-has-advanced-tech-and-time-travel-but-is-always-at-war-with-the-past/Chrono-Industrial Zone.json"
style_text = """scifi, futuristic, illustration, high contrast, cinematic, detailed, atmospheric, 8k, by Jim Burns"""

f_json = "../results/advanced/refugees-that-have-crash-landed-after-their-planet-was-destroyed-by-an-ecological-disaster/Tyrosia.json"
style_text = """scifi, futuristic, illustration, dark, cinematic, detailed, atmospheric, 8k, by feng zhu, concept art"""


f_json = "../results/advanced/gothic-world-with-very-low-technology-vampires-and-dark-spirits-roam-the-world-but-there-is-very-little-magic-for-others-the-humans-live-in-fear-crowded-in-small-filthy-villages/Blackwood.json"
style_text = """Illustration by Jeffrey Catherine Jones. Evil, forboding, detailed, scary, cinematic"""


neg_text = """((sfw)), easynegative, badhandv4, greyscale, monochrome, water mark, signature, bad anatomy, bad proportions, deformed, poorly drawn hands, extra fingers, extra limbs, blurry"""


def load_world(f_json):
    with open(f_json) as FIN:
        js = json.load(FIN)

    world = js["world"]
    return world


world = load_world(f_json)

IGNORED_KEYS = [
    "name",
    "description",
    "basic_city_desc",
    "residents",
    "languages",
]


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


subareas = ["races", "creatures", "landmarks", "lore"]
ITR = []


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

save_dest = Path("results") / world["name"]
save_dest.mkdir(exist_ok=True, parents=True)

df = pd.DataFrame(data=ITR, columns=["key", "prompt"])
df["f_save"] = [save_dest / f"{k:06d}.png" for k in range(len(df))]

# Save the result
f_csv = Path("results") / (world["name"] + ".csv")
df.to_csv(f_csv, index=False)


# Only generate the new images
idx = np.array([x.exists() for x in df.f_save])
df = df[~idx]
df["negative_prompt"] = neg_text
df["style_prompt"] = style_text


# Exit peacefully if no work is needed
if not len(df):
    print("All done!")
    exit(0)

###############################################################################

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
    save_dest = Path(".") / "stable-diffusion-webui" / "log" / "images"
    for f in save_dest.glob("*.png"):
        if f.is_file():
            f.unlink()

    # Generate the image
    ID = driver.find_element(By.ID, "txt2img_generate_box")
    inputbox = ID.find_elements(By.TAG_NAME, "button")[2]
    inputbox.click()
    WebDriverWait(driver, 10)
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


for f_save, prompt in tqdm(zip(df.f_save, df.prompt), total=len(df)):
    f_png = generate_image(prompt, neg_text, style_text)
    f_png.rename(f_save)
    print(f_save)

# Finish up and shutdown
driver.close()
driver.quit()
