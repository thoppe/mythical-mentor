import os
from worldbuilder.utils import load_multi_yaml

f_templates = "templates.yaml"
programs = load_multi_yaml(f_templates)
for name in programs:
    if name == "template":
        continue

    os.system(f"python P0_build_world.py --topic '{name}'")
    os.system(f"python P1_build_cities.py --topic '{name}'")
    os.system(f"python Q0_generate_images.py --topic '{name}'")
    os.system("python Q1_downscale_images.py")
    os.system(f"python Q2_build_hyperlinks.py --topic '{name}'")


os.system("python Q1_downscale_images.py")
