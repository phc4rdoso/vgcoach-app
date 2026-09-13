from pydantic import BaseModel
from typing import List

class Regulation(BaseModel):
    name: str
    description: str
    banned_pokemon: List[str] = []
    restricted_legendaries_allowed: int = 0

REGULATIONS = {
    "Regulation H": Regulation(
        name="Regulation H",
        description="No Restricted Legendaries, No Minor Legendaries (Treasures of Ruin, Ogerpon, Loyal Three, Pecharunt), and No Paradox Pokémon.",
        restricted_legendaries_allowed=0
    ),
    "Regulation G": Regulation(
        name="Regulation G",
        description="Up to one Restricted Legendary allowed per team (e.g., Calyrex, Koraidon, Miraidon).",
        restricted_legendaries_allowed=1
    ),
    "Regulation F": Regulation(
        name="Regulation F",
        description="All Pokémon in the Paldea, Kitakami, and Blueberry Pokédexes allowed. No Restricted Legendaries.",
        restricted_legendaries_allowed=0
    ),
    "Regulation E": Regulation(
        name="Regulation E",
        description="Kitakami Pokédex allowed. No Restricted Legendaries.",
        restricted_legendaries_allowed=0
    ),
    "Regulation D": Regulation(
        name="Regulation D",
        description="Pokémon HOME transfers allowed. No Restricted Legendaries.",
        restricted_legendaries_allowed=0
    )
}

def get_regulation(name: str) -> Regulation:
    return REGULATIONS.get(name, REGULATIONS["Regulation H"])

def get_all_regulation_names() -> List[str]:
    return list(REGULATIONS.keys())
