
#topic = "chickens"
#topic = "amazonian_justice"
#topic = "gothic"
topic = "archipelago"

all:
	python P0_build_world.py --topic $(topic) 
	python P1_build_cities.py --topic $(topic)
	python Q0_generate_images.py --topic $(topic)
	python Q1_downscale_images.py
	python Q2_build_hyperlinks.py --topic $(topic)

lint:
	black *.py imgs worldbuilder --line-length 80
	flake8 *.py imgs worldbuilder --ignore=E501,W503

streamlit:
	streamlit run streamlit_app.py
