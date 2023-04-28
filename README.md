# Mythical Mentor
Use AI to generate worlds and mythos automatically

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