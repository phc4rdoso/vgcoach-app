import requests
import gzip
import json
import io
import re
import streamlit as st
from src.pokeapi import get_pokemon_data, get_move_type, get_move_damage_class

@st.cache_data(ttl=86400) # Cache for 1 day
def fetch_top_meta_pokemon(regulation_name: str):
    try:
        # Convert "Regulation M-C" -> "regmc", "Regulation H" -> "regh"
        shortcode = regulation_name.lower().replace(" ", "").replace("-", "")
        if shortcode.startswith("regulation"):
            shortcode = shortcode.replace("regulation", "reg")
            
        res = requests.get('https://www.smogon.com/stats/')
        months = sorted(re.findall(r'href="(\d{4}-\d{2}/)"', res.text), reverse=True)
        if not months:
            return fallback_meta()
            
        for month in months:
            # We don't want to check thousands of months, check maximum 6 past months
            if months.index(month) > 5:
                break
                
            chaos_url = f'https://www.smogon.com/stats/{month}chaos/'
            res2 = requests.get(chaos_url)
            
            # Look for file matching the shortcode
            files = re.findall(rf'href="([^"]*{shortcode}[^"]*\.json\.gz)"', res2.text)
            
            if files:
                # Prioritize highest rating
                best_file = sorted(files)[-1]
                
                # Download and extract
                gz_res = requests.get(f'{chaos_url}{best_file}')
                decompressed = gzip.GzipFile(fileobj=io.BytesIO(gz_res.content)).read().decode('utf-8')
                data = json.loads(decompressed)
                
                # Extract top 30
                top_pokemon = sorted(data['data'].items(), key=lambda x: x[1]['usage'], reverse=True)[:30]
                
                meta_list = []
                for name, stats in top_pokemon:
                    moves = sorted(stats['Moves'].items(), key=lambda x: x[1], reverse=True)
                    meta_list.append({
                        "species": name,
                        "moves": [m[0] for m in moves if m[0]]
                    })
                    
                return meta_list
                
        # If we didn't find the specific regulation in the last 6 months, return fallback
        print(f"Could not find regulation {regulation_name} ({shortcode}) in recent Smogon stats.")
        return fallback_meta()
        
    except Exception as e:
        print(f"Failed to fetch meta: {e}")
        return fallback_meta()

def fallback_meta():
    return [{"species": p, "moves": []} for p in ['Kingambit', 'Incineroar', 'Garchomp', 'Basculegion', 'Sneasler', 'Charizard-Mega-Y', 'Sinistcha', 'Whimsicott', 'Farigiraf', 'Sylveon', 'Floette-Mega', 'Staraptor-Mega', 'Delphox-Mega', 'Raichu-Mega-Y', 'Blastoise-Mega', 'Archaludon', 'Venusaur', 'Pelipper', 'Froslass-Mega', 'Aerodactyl-Mega', 'Gholdengo', 'Swampert-Mega', 'Grimmsnarl', 'Ninetales-Alola', 'Gengar-Mega', 'Milotic', 'Arcanine-Hisui', 'Maushold', 'Dragonite-Mega', 'Scovillain-Mega']]

# Type effectiveness chart
TYPE_EFFECTIVENESS = {
    "normal": {"rock": 0.5, "ghost": 0, "steel": 0.5},
    "fire": {"fire": 0.5, "water": 0.5, "grass": 2, "ice": 2, "bug": 2, "rock": 0.5, "dragon": 0.5, "steel": 2},
    "water": {"fire": 2, "water": 0.5, "grass": 0.5, "ground": 2, "rock": 2, "dragon": 0.5},
    "electric": {"water": 2, "electric": 0.5, "grass": 0.5, "ground": 0, "flying": 2, "dragon": 0.5},
    "grass": {"fire": 0.5, "water": 2, "grass": 0.5, "poison": 0.5, "ground": 2, "flying": 0.5, "bug": 0.5, "rock": 2, "dragon": 0.5, "steel": 0.5},
    "ice": {"fire": 0.5, "water": 0.5, "grass": 2, "ice": 0.5, "ground": 2, "flying": 2, "dragon": 2, "steel": 0.5},
    "fighting": {"normal": 2, "ice": 2, "poison": 0.5, "flying": 0.5, "psychic": 0.5, "bug": 0.5, "rock": 2, "ghost": 0, "dark": 2, "steel": 2, "fairy": 0.5},
    "poison": {"grass": 2, "poison": 0.5, "ground": 0.5, "rock": 0.5, "ghost": 0.5, "steel": 0, "fairy": 2},
    "ground": {"fire": 2, "water": 1, "electric": 2, "grass": 0.5, "poison": 2, "flying": 0, "bug": 0.5, "rock": 2, "steel": 2},
    "flying": {"electric": 0.5, "grass": 2, "fighting": 2, "bug": 2, "rock": 0.5, "steel": 0.5},
    "psychic": {"fighting": 2, "poison": 2, "psychic": 0.5, "dark": 0, "steel": 0.5},
    "bug": {"fire": 0.5, "grass": 2, "fighting": 0.5, "poison": 0.5, "flying": 0.5, "psychic": 2, "ghost": 0.5, "dark": 2, "steel": 0.5, "fairy": 0.5},
    "rock": {"fire": 2, "ice": 2, "fighting": 0.5, "ground": 0.5, "flying": 2, "bug": 2, "steel": 0.5},
    "ghost": {"normal": 0, "psychic": 2, "ghost": 2, "dark": 0.5},
    "dragon": {"dragon": 2, "steel": 0.5, "fairy": 0},
    "dark": {"fighting": 0.5, "psychic": 2, "ghost": 2, "dark": 0.5, "fairy": 0.5},
    "steel": {"fire": 0.5, "water": 0.5, "electric": 0.5, "ice": 2, "rock": 2, "steel": 0.5, "fairy": 2},
    "fairy": {"fire": 0.5, "fighting": 2, "poison": 0.5, "dragon": 2, "dark": 2, "steel": 0.5}
}

def get_multiplier(attack_type, defend_types):
    mult = 1.0
    for dt in defend_types:
        if attack_type in TYPE_EFFECTIVENESS and dt in TYPE_EFFECTIVENESS[attack_type]:
            mult *= TYPE_EFFECTIVENESS[attack_type][dt]
    return mult

def analyze_meta_threats(team, regulation_name: str):
    top_meta = fetch_top_meta_pokemon(regulation_name)
    threats = []
    
    # Pre-calculate team types and abilities
    team_data = []
    team_abilities = set()
    for p in team.pokemons:
        if p.ability:
            team_abilities.add(p.ability.lower().replace(" ", ""))
        data = get_pokemon_data(p.species)
        if data:
            team_data.append({
                "species": p.species,
                "types": data["types"],
                "ability": p.ability.lower().replace(" ", "") if p.ability else "",
                "moves": p.moves
            })
            
    for meta_item in top_meta:
        meta_species = meta_item["species"]
        meta_moves = meta_item["moves"]
        
        sanitized_species = meta_species.lower()
        if sanitized_species == "urshifu-rapid-strike": sanitized_species = "urshifu-rapid-strike"
        if sanitized_species == "urshifu": sanitized_species = "urshifu-single-strike"
        
        meta_data = get_pokemon_data(sanitized_species)
        if not meta_data:
            continue
            
        meta_types = meta_data["types"]
        meta_abilities = meta_data.get("abilities", [])
        
        # Get top 4 damaging move types for coverage
        meta_coverage_types = []
        for move in meta_moves:
            dmg_class = get_move_damage_class(move)
            if dmg_class in ["physical", "special"]:
                m_type = get_move_type(move)
                if m_type and m_type not in meta_coverage_types:
                    meta_coverage_types.append(m_type)
            if len(meta_coverage_types) >= 4:
                break
                
        if not meta_coverage_types:
            meta_coverage_types = meta_types
        
        # Calculate Threat Score
        hits_team_se = [] 
        team_hits_se = [] 
        
        for t_mon in team_data:
            # Can meta hit team mon SE?
            max_meta_mult = 1.0
            for mt in meta_coverage_types:
                mult = get_multiplier(mt.lower(), [t.lower() for t in t_mon["types"]])
                if mult > max_meta_mult:
                    max_meta_mult = mult
            if max_meta_mult >= 2.0:
                hits_team_se.append(t_mon["species"])
                
            # Can team mon hit meta SE?
            max_team_mult = 1.0
            move_types = []
            if t_mon.get("moves"):
                for m in t_mon["moves"]:
                    m_type = get_move_type(m)
                    if m_type:
                        move_types.append(m_type)
            if not move_types:
                move_types = t_mon["types"] # Fallback to STAB if no attacking moves
                
            for tt in move_types:
                mult = get_multiplier(tt.lower(), [t.lower() for t in meta_types])
                if mult > max_team_mult:
                    max_team_mult = mult
            if max_team_mult >= 2.0:
                team_hits_se.append(t_mon["species"])
                
        # Ability Threats
        ability_threat_msg = ""
        is_ability_threat = False
        
        if "intimidate" in team_abilities:
            if "defiant" in meta_abilities:
                ability_threat_msg = "Punishes your Intimidate with Defiant (+2 Atk)."
                is_ability_threat = True
            elif "competitive" in meta_abilities:
                ability_threat_msg = "Punishes your Intimidate with Competitive (+2 SpA)."
                is_ability_threat = True
                
        if "drizzle" in team_abilities and "swiftswim" in meta_abilities:
            ability_threat_msg = "Uses your Rain to activate Swift Swim (double Speed)."
            is_ability_threat = True
            
        if "drought" in team_abilities and ("chlorophyll" in meta_abilities or "protosynthesis" in meta_abilities):
            ability_threat_msg = "Uses your Sun to activate Chlorophyll/Protosynthesis."
            is_ability_threat = True
            
        if "snowwarning" in team_abilities and "slushrush" in meta_abilities:
            ability_threat_msg = "Uses your Snow to activate Slush Rush (double Speed)."
            is_ability_threat = True
            
        if "sandstream" in team_abilities and "sandrush" in meta_abilities:
            ability_threat_msg = "Uses your Sand to activate Sand Rush (double Speed)."
            is_ability_threat = True
            
        if "electricsurge" in team_abilities and "quarkdrive" in meta_abilities:
            ability_threat_msg = "Uses your Electric Terrain to activate Quark Drive."
            is_ability_threat = True
                
        # Ensure uniqueness in lists just in case
        hits_team_se = list(set(hits_team_se))
        team_hits_se = list(set(team_hits_se))
        
        if (len(hits_team_se) >= 2 and len(team_hits_se) <= 1) or is_ability_threat:
            # Construct explanation
            explanation = ""
            if hits_team_se:
                explanation += f"Hits {', '.join(hits_team_se)} for Super Effective damage."
                if not team_hits_se:
                    explanation += " No one on your team can hit it for SE damage!"
                else:
                    explanation += f" Only {team_hits_se[0]} can hit it for SE damage."
            elif is_ability_threat:
                explanation += "Has a dangerous ability matchup against your team."
                
            if ability_threat_msg:
                explanation += f" {ability_threat_msg}"
                
            threats.append({
                "species": meta_species,
                "sprite": meta_data.get("sprite", ""),
                "hits_team": hits_team_se,
                "team_hits_it": team_hits_se,
                "score": len(hits_team_se) - len(team_hits_se) + (2 if is_ability_threat else 0),
                "explanation": explanation.strip()
            })
            
    return threats
