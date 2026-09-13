import requests
from typing import Dict, Any, Tuple, List
import functools

@functools.lru_cache(maxsize=128)
def get_pokemon_data(species_name: str) -> Dict[str, Any]:
    """
    Fetches base stats and types for a given Pokemon species from PokeAPI.
    Cleans up the name to match PokeAPI formats (e.g., flutter-mane).
    """
    clean_name = species_name.lower().replace(" ", "-").replace("'", "").replace(".", "")
    # Handle forms if necessary (e.g., ogerpon-hearthflame)
    
    url = f"https://pokeapi.co/api/v2/pokemon/{clean_name}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}
            # Map pokeapi stat names to our format
            mapped_stats = {
                "HP": stats.get("hp", 0),
                "Atk": stats.get("attack", 0),
                "Def": stats.get("defense", 0),
                "SpA": stats.get("special-attack", 0),
                "SpD": stats.get("special-defense", 0),
                "Spe": stats.get("speed", 0)
            }
            types = [t['type']['name'].capitalize() for t in data['types']]
            sprite = data.get('sprites', {}).get('front_default', "")
            return {"stats": mapped_stats, "types": types, "sprite": sprite}
    except Exception as e:
        print(f"Error fetching {species_name}: {e}")
        
    # Return safe defaults if not found
    return {"stats": {"HP": 100, "Atk": 100, "Def": 100, "SpA": 100, "SpD": 100, "Spe": 100}, "types": ["Normal"], "sprite": ""}

def calculate_stat(base: int, ev: int, iv: int, level: int, is_hp: bool, nature_multiplier: float = 1.0) -> int:
    """Calculates the actual stat of a Pokemon."""
    if is_hp:
        return int(((2 * base + iv + (ev // 4)) * level) / 100) + level + 10
    else:
        stat_val = int(((2 * base + iv + (ev // 4)) * level) / 100) + 5
        return int(stat_val * nature_multiplier)

NATURE_MODIFIERS = {
    "Adamant": {"Atk": 1.1, "SpA": 0.9},
    "Bold": {"Def": 1.1, "Atk": 0.9},
    "Brave": {"Atk": 1.1, "Spe": 0.9},
    "Calm": {"SpD": 1.1, "Atk": 0.9},
    "Careful": {"SpD": 1.1, "SpA": 0.9},
    "Impish": {"Def": 1.1, "SpA": 0.9},
    "Jolly": {"Spe": 1.1, "SpA": 0.9},
    "Modest": {"SpA": 1.1, "Atk": 0.9},
    "Quiet": {"SpA": 1.1, "Spe": 0.9},
    "Relaxed": {"Def": 1.1, "Spe": 0.9},
    "Sassy": {"SpD": 1.1, "Spe": 0.9},
    "Timid": {"Spe": 1.1, "Atk": 0.9},
}

def get_nature_multiplier(nature: str, stat_name: str) -> float:
    mods = NATURE_MODIFIERS.get(nature, {})
    return mods.get(stat_name, 1.0)
