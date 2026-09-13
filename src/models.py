from pydantic import BaseModel
from typing import List, Optional, Dict

class Pokemon(BaseModel):
    species: str
    item: Optional[str] = None
    ability: Optional[str] = None
    level: int = 50
    tera_type: Optional[str] = None
    evs: Dict[str, int] = {"HP": 0, "Atk": 0, "Def": 0, "SpA": 0, "SpD": 0, "Spe": 0}
    ivs: Dict[str, int] = {"HP": 31, "Atk": 31, "Def": 31, "SpA": 31, "SpD": 31, "Spe": 31}
    nature: str = "Hardy"
    moves: List[str] = []
    gender: Optional[str] = None
    shiny: bool = False

class Team(BaseModel):
    pokemons: List[Pokemon] = []
