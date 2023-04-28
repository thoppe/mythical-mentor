import json
import streamlit as st
import pandas as pd
from pathlib import Path
import uuid
import itertools
from PIL import Image

st.set_page_config(
    layout="centered",
    page_icon=":new_moon_with_face:",
    page_title="Mythical Mentor",
)

load_dest = Path("results") / "advanced"
F_JSON = sorted(list(load_dest.glob("**/*.json")))
NAMES = sorted(list(set([x.stem.split("_")[0] for x in F_JSON]))[::-1])


def reset_all():
    del st.session_state["hierarchy"]


def nav_button_callback(topic):
    st.session_state["hierarchy"].append(topic)


def button_go_back():
    st.session_state["hierarchy"].pop()


with st.sidebar:

    starting_index = 3

    category = st.selectbox(
        "World", NAMES, on_change=reset_all, index=starting_index
    )
    f_json = [x for x in F_JSON if category in str(x)][0]


# @st.cache_resource
def load_data(f_json):

    with open(f_json) as FIN:
        js = json.load(FIN)

    return js


js = load_data(f_json)
world = js["world"]

if "meta" in js:
    starter_prompt = js["meta"]["main_topic"]
    schema_version = int(js["meta"]["mythical_mentor_schema_version"])
else:
    # Old code to remove
    starter_prompt = js["prompts"]["world_names"]
    starter_prompt = starter_prompt.split("designing a")[1]
    starter_prompt = starter_prompt.split("Enumerate names")[0]
    starter_prompt = starter_prompt.strip().strip(".").strip()
    schema_version = 1


IGNORED_KEYS = ["name", "description", "basic_city_desc", "residents"]

if "hierarchy" not in st.session_state:
    st.session_state["hierarchy"] = []

hi = st.session_state["hierarchy"]

# Define the app title and description
world_name = world["name"]
st.write(f"# {world_name}")
st.write(f"_{starter_prompt}_")

# Check if we have a img picture
f_world_csv = Path("imgs") / "results" / f"{world_name}.csv"
if f_world_csv.exists():
    dx = pd.read_csv(f_world_csv)
    dx = dx.sort_values("key")
    dx["key"] = [" ".join((eval(x))) for x in dx["key"]]
else:
    dx = pd.DataFrame(columns=["key", "f_save", "prompt"])


def write_images(img_key, dx, show_description=True):
    if not isinstance(img_key, str):
        img_key = " ".join(img_key)
    dx2 = dx[dx["key"] == img_key]
    for f, text in zip(dx2.f_save, dx2.prompt):

        f_img = Path("imgs") / f

        if not f_img.exists():
            f_img = f_img.with_suffix(".jpg")

        if f_img.exists():
            img = Image.open(f_img)
            st.image(img, width=400)

        if show_description:
            st.write(text)


if len(hi) > 0:
    st.button(":arrow_left: Go back", type="secondary", on_click=button_go_back)
    st.sidebar.button(
        ":arrow_left: Go back",
        type="secondary",
        on_click=button_go_back,
        key="GOBACK2",
    )

for k, key in enumerate(hi):
    header = "#" * (k + 2)
    text_key = key
    if len(text_key.split()) == 1:
        text_key = text_key.title()
    st.write(f"{header} {text_key}")
    world = world[key]


if "description" not in world:
    write_images(hi, dx)

if not isinstance(world, str):
    cols = itertools.cycle(st.columns(3))
    keys = [key for key in world.keys() if key not in IGNORED_KEYS]

    buttons = []
    location = st

    for col, key in zip(cols, keys):

        if len(hi) == 0 or (len(hi) >= 2 and hi[-2] == "cities"):
            location = col

        img_key = " ".join(hi + [key, "description"])
        write_images(img_key, dx, show_description=False)

        if len(hi) >= 2 and hi[-1] == "inhabitants":
            write_images(
                hi + [key],
                dx,
                show_description=False,
            )

        button = location.button(
            key,
            on_click=nav_button_callback,
            key=uuid.uuid4(),
            args=(key,),
        )
        buttons.append(button)

else:
    if len(dx) == 0 or hi[-1] == "languages":
        world


if "description" in world:

    # Look for an image
    write_images(hi + ["description"], dx)
    st.write(world["description"])


st.write(
    """
   *Use the sidebar to select different worlds.*
   Made with 💙 by [@metasemantic](https://twitter.com/metasemantic),
"""
)


with st.sidebar.expander("meta"):
    st.write(f"_Mythical schema version: {schema_version:d}_")


#   [code](https://github.com/thoppe/autology).
