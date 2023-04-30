# Mythical Mentor
Use AI to generate worlds and mythos automatically.

```mermaid
flowchart TD
    WName(World Name) --> WorldDesc(World Description)
    WorldDesc --> Races
    Races --> Creatures
    Races --> Cities
    WorldDesc --> Deities
    
    Deities --> Beliefs
    Deities --> Landmarks
    Races --> Landmarks

    subgraph city [ ]
      Cities --> CITY1(City Description)
      CITY1 --> CITY2(City Residents)
      CITY2 --> CITY3(City Lore)
    end
```

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://thoppe-mythical-mentor-streamlit-app-4taw1v.streamlit.app/)

### To do

+ Allow for different SD models
+ Add in real hyperlinks in the app