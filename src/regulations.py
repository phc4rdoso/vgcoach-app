import requests
from pydantic import BaseModel
from typing import List, Dict

class Regulation(BaseModel):
    name: str
    description: str
    banned_pokemon: List[str] = []
    allowed_items: List[str] = []
    restricted_legendaries_allowed: int = 0

# Default mock rulesets in case the external API is unreachable
DEFAULT_REGULATIONS = {
    "Regulation M-C": Regulation(
        name="Regulation M-C",
        description="Pokémon Champions Regulation M-C. Includes Mega Evolutions. 2 Restricted Legendaries allowed.",
        restricted_legendaries_allowed=2
    ),
    "Regulation M-B": Regulation(
        name="Regulation M-B",
        description="Pokémon Champions Regulation M-B. 1 Restricted Legendary allowed.",
        restricted_legendaries_allowed=1
    ),
    "Regulation M-A": Regulation(
        name="Regulation M-A",
        description="Pokémon Champions Regulation M-A. Regional Dex only, no Restricted Legendaries.",
        restricted_legendaries_allowed=0
    ),
}

_regulations_cache: Dict[str, Regulation] = {}

def fetch_regulations() -> Dict[str, Regulation]:
    """
    Fetches the latest Pokémon Champions regulations from a trusted external service.
    Falls back to defaults if the service is unreachable.
    """
    global _regulations_cache
    if _regulations_cache:
        return _regulations_cache
        
    api_url = "https://api.pokemon-champions.com/v1/regulations"  # Placeholder external service
    try:
        # In a real scenario, this fetches the live JSON from the VGC API
        response = requests.get(api_url, timeout=2)
        if response.status_code == 200:
            data = response.json()
            fetched = {}
            for reg_data in data.get("regulations", []):
                fetched[reg_data["name"]] = Regulation(**reg_data)
            _regulations_cache = fetched
            return fetched
    except requests.exceptions.RequestException:
        print("Warning: Could not reach trusted external service. Using fallback regulations.")
        
    _regulations_cache = DEFAULT_REGULATIONS
    return _regulations_cache

def get_regulation(name: str) -> Regulation:
    regs = fetch_regulations()
    return regs.get(name, DEFAULT_REGULATIONS["Regulation M-C"])

def get_all_regulation_names() -> List[str]:
    return list(fetch_regulations().keys())
