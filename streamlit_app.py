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

load_dest = Path("results") / "worldbuilding"
F_JSON = sorted(list(load_dest.glob("**/*.json")))

@st.cache_resource 
def load_data(F_JSON):
    JS = [json.load(open(f)) for f in F_JSON]
    return JS


JS = load_data(F_JSON)
NAMES = [js["meta"]["world_name"] for js in JS]


def reset_all():
    del st.session_state["hierarchy"]


def nav_button_callback(topic):
    st.session_state["hierarchy"].append(topic)


def button_go_back():
    st.session_state["hierarchy"].pop()


with st.sidebar:
    starting_index = 1

    category = st.selectbox(
        "World", NAMES, on_change=reset_all, index=starting_index
    )

js = JS[NAMES.index(category)]
world = js["content"]
starter_prompt = js["meta"]["main_topic"]
schema_version = int(js["meta"]["mythical_mentor_schema_version"])

IGNORED_KEYS = [
    "world_description",
    "world_names",
    "basic_cities",
    "city_description",
    "basic_residents",
]
DESCRIPTION_KEYS = [
    "world_description",
    "city_description",
]

if "hierarchy" not in st.session_state:
    st.session_state["hierarchy"] = []

hi = st.session_state["hierarchy"]

# Define the app title and description
world_name = js["meta"]["world_name"]

st.write(f"# {world_name}")
st.write(f"_{starter_prompt.capitalize()}_")

# Check if we have a img picture
f_world_csv = Path("results") / "images" / f"{world_name}.csv"
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

    for f_img, text in zip(dx2.f_save, dx2.prompt):
        f_img = Path(f_img)

        # st.write("HERE", f_img)

        if not f_img.exists():
            f_img = f_img.with_suffix(".jpg")

        if f_img.exists():
            img = Image.open(f_img)
            st.image(img, width=400)

        if show_description:
            st.write(text)


extended_hi = " : ".join([world_name] + hi)

if len(hi) > 0:
    st.button(":arrow_left: Go back", type="secondary", on_click=button_go_back)
    st.sidebar.button(
        ":arrow_left: Go back",
        type="secondary",
        on_click=button_go_back,
        key="go_back_button_key",
    )
    st.sidebar.write(f"_{extended_hi}_")

st.write(f"### {extended_hi}")
for k, key in enumerate(hi):
    world = world[key]

if not any([x in world for x in DESCRIPTION_KEYS]):
    write_images(hi, dx)

####################################################################

if not isinstance(world, str):
    cols = itertools.cycle(st.columns(3))
    keys = [key for key in world.keys() if key not in IGNORED_KEYS]

    buttons = []
    location = st

    for col, key in zip(cols, keys):

        if len(hi) == 0 or (len(hi) >= 2 and hi[-2] == "cities"):
            location = col

        img_key = ""

        if hi:
            if hi[-1] == "cities":
                img_key = " ".join(hi + [key, "city_description"])
            elif hi[-1] == "residents":
                img_key = " ".join(
                    hi
                    + [
                        key,
                    ]
                )

        write_images(img_key, dx, show_description=False)

        button = location.button(
            key,
            on_click=nav_button_callback,
            key=uuid.uuid4(),
            args=(key,),
        )
        buttons.append(button)

else:
    if len(dx) == 0:
        world


for key in DESCRIPTION_KEYS:
    if key in world:
        # Look for an image
        write_images(hi + [key], dx)
        st.write(world[key])


st.write(
    """
   *Use the sidebar to select different worlds.*
   Made with 💙 by [@metasemantic](https://twitter.com/metasemantic),
"""
)

# with st.sidebar.expander("meta"):
#    st.write(f"_Mythical schema version: {schema_version:d}_")
#   [code](https://github.com/thoppe/autology).
