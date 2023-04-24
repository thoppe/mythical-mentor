#topic = "High fantasy world recovering after the great sundering"
#topic = "Steampunk world that has advanced tech and time travel, but is always at war with the past "
#topic = "Refugees that have crash landed after their planet was destroyed by an ecological disaster."
#topic = "Magical world set on an archipelago with perpetual auroras, geopolitics, magic weather, fanatical religious sects, freeholders, and gangs."
topic = "Gothic world with very low technology. Vampires and dark spirits roam the world, but there is very little magic for others. The humans live in fear crowded in small, filthy, villages."

all:
	python P0_build_world.py --topic $(topic)
	python P1_build_cities.py --topic $(topic)
#	cd imgs/ && python P0_generate_images.py
	cd imgs/ && python imgs/P1_spindown_images.py

lint:
	black *.py imgs --line-length 80
	flake8 *.py imgs --ignore=E501

streamlit:
	streamlit run streamlit_app.py
