import requests
from functools import lru_cache
from typing import Dict, Any, Tuple, List
import functools

@functools.lru_cache(maxsize=128)
def get_pokemon_data(species_name: str) -> Dict[str, Any]:
    """
    Fetches base stats and types for a given Pokemon species from PokeAPI.
    Cleans up the name to match PokeAPI formats (e.g., flutter-mane).
    """
    clean_name = species_name.lower().replace(" ", "-").replace("'", "").replace(".", "")
    
    NAME_MAP = {
        "basculegion": "basculegion-male",
        "basculegion-m": "basculegion-male",
        "basculegion-f": "basculegion-female",
        "indeedee": "indeedee-male",
        "indeedee-m": "indeedee-male",
        "indeedee-f": "indeedee-female",
        "meowstic": "meowstic-male",
        "meowstic-m": "meowstic-male",
        "meowstic-f": "meowstic-female",
        "oinkologne": "oinkologne-male",
        "oinkologne-m": "oinkologne-male",
        "oinkologne-f": "oinkologne-female",
        "palafin": "palafin-hero",
        "urshifu": "urshifu-single-strike",
        "tornadus": "tornadus-incarnate",
        "thundurus": "thundurus-incarnate",
        "landorus": "landorus-incarnate",
        "enamorus": "enamorus-incarnate",
        "giratina": "giratina-altered",
        "shaymin": "shaymin-land",
        "keldeo": "keldeo-ordinary",
        "aegislash": "aegislash-shield",
        "pumpkaboo": "pumpkaboo-average",
        "gourgeist": "gourgeist-average",
        "toxtricity": "toxtricity-amped",
        "eiscue": "eiscue-ice",
        "morpeko": "morpeko-full-belly",
        "darmanitan": "darmanitan-standard",
        "darmanitan-galar": "darmanitan-galar-standard",
        "meloetta": "meloetta-aria",
        "lycanroc": "lycanroc-midday",
        "wishiwashi": "wishiwashi-solo",
        "minior": "minior-red-meteor",
        "ogerpon-wellspring": "ogerpon-wellspring-mask",
        "ogerpon-hearthflame": "ogerpon-hearthflame-mask",
        "ogerpon-cornerstone": "ogerpon-cornerstone-mask",
        "tauros-paldea-combat": "tauros-paldea-combat-breed",
        "tauros-paldea-blaze": "tauros-paldea-blaze-breed",
        "tauros-paldea-aqua": "tauros-paldea-aqua-breed",
        "tauros-paldea": "tauros-paldea-combat-breed",
        "zacian": "zacian",
        "zamazenta": "zamazenta"
    }
    
    if clean_name in NAME_MAP:
        clean_name = NAME_MAP[clean_name]
        
    original_clean_name = clean_name
    use_showdown_sprite = False
    
    if clean_name.endswith("-mega-z") or clean_name.endswith("-mega-x") or clean_name.endswith("-mega-y"):
        clean_name = clean_name[:-2] # removes -z, -x, -y
        use_showdown_sprite = True
    
    # Some megas don't exist in pokeapi if they are fan-made, so fallback to base species if needed
    url = f"https://pokeapi.co/api/v2/pokemon/{clean_name}"
    
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 404 and "-" in clean_name:
            # Fallback to base species if form not found
            clean_name = clean_name.split("-")[0]
            url = f"https://pokeapi.co/api/v2/pokemon/{clean_name}"
            res = requests.get(url, timeout=5)
            use_showdown_sprite = True
            
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
            if use_showdown_sprite:
                # Format for showdown e.g. garchomp-mega-z -> garchomp-megaz
                sd_name = original_clean_name.replace("-mega-z", "-megaz").replace("-mega-x", "-megax").replace("-mega-y", "-megay")
                sprite = f"https://play.pokemonshowdown.com/sprites/gen5/{sd_name}.png"
                
            abilities = [a['ability']['name'].lower() for a in data.get('abilities', [])]
            return {"stats": mapped_stats, "types": types, "sprite": sprite, "abilities": abilities}
    except Exception as e:
        print(f"Error fetching {species_name}: {e}")
        
    # Return safe defaults if not found
    return {"stats": {"HP": 100, "Atk": 100, "Def": 100, "SpA": 100, "SpD": 100, "Spe": 100}, "types": ["Normal"], "sprite": "", "abilities": []}

@lru_cache(maxsize=100)
def get_move_damage_class(move_name: str) -> str:
    """Fetches the damage class ('physical', 'special', 'status') of a given move."""
    try:
        if not move_name or move_name == "Protect":
            return 'status'
        formatted_name = move_name.lower().replace(" ", "-").replace("'", "").replace("%", "")
        res = requests.get(f"https://pokeapi.co/api/v2/move/{formatted_name}")
        if res.status_code == 200:
            data = res.json()
            return data.get('damage_class', {}).get('name', 'status')
    except Exception as e:
        print(f"Error fetching damage class for {move_name}: {e}")
    return 'status'

@lru_cache(maxsize=100)
def get_move_type(move_name: str) -> str:
    """Fetches the type of a given move from PokeAPI. Returns None if it is a status move."""
    try:
        if not move_name or move_name == "Protect":
            return None
        formatted_name = move_name.lower().replace(" ", "-").replace("'", "").replace("%", "")
        res = requests.get(f"https://pokeapi.co/api/v2/move/{formatted_name}")
        if res.status_code == 200:
            data = res.json()
            if data.get('damage_class', {}).get('name') == 'status':
                return None
            return data['type']['name'].capitalize()
    except Exception as e:
        print(f"Error fetching move {move_name}: {e}")
    return None

@lru_cache(maxsize=100)
def is_spread_damage(move_name: str) -> bool:
    """Checks if a move is a spread damage move (hits multiple targets and is an attack)."""
    try:
        if not move_name or move_name == "Protect":
            return False
        formatted_name = move_name.lower().replace(" ", "-").replace("'", "").replace("%", "")
        res = requests.get(f"https://pokeapi.co/api/v2/move/{formatted_name}")
        if res.status_code == 200:
            data = res.json()
            if data.get('damage_class', {}).get('name') == 'status':
                return False
            target_name = data.get('target', {}).get('name', '')
            if target_name in ['all-opponents', 'all-other-pokemon']:
                return True
    except Exception as e:
        print(f"Error fetching move {move_name}: {e}")
    return False

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
