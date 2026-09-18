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
            return fallback_meta(), 'Smogon stats API is currently unreachable or has no data. Falling back to local offline snapshot.'
            
        def find_best_file(pattern):
            for month in months[:6]:
                moveset_url = f'https://www.smogon.com/stats/{month}moveset/'
                res2 = requests.get(moveset_url)
                files = re.findall(pattern, res2.text)
                if files:
                    return moveset_url, sorted(files)[-1]
            return None, None
            
        is_exact = True
        # 1. Try shortcode with bo3
        url, best_file = find_best_file(rf'href="([^"]*{shortcode}[^"]*bo3[^"]*\.txt\.gz)"')
        
        if not url:
            # 2. Try shortcode without bo3
            url, best_file = find_best_file(rf'href="([^"]*{shortcode}[^"]*\.txt\.gz)"')
            
        if not url:
            is_exact = False
            # 3. Fallback to any gen9 vgc bo3
            url, best_file = find_best_file(r'href="([^"]*gen9[^"]*vgc[^"]*bo3[^"]*\.txt\.gz)"')
            
        if not url:
            is_exact = False
            # 4. Fallback to any gen9 vgc
            url, best_file = find_best_file(r'href="([^"]*gen9[^"]*vgc[^"]*\.txt\.gz)"')
            
        if url and best_file:
            # Download and extract
            gz_res = requests.get(f'{url}{best_file}')
            text = gzip.GzipFile(fileobj=io.BytesIO(gz_res.content)).read().decode('utf-8')
            
            meta_list = []
            lines = text.split('\n')
            current_species = None
            in_moves = False
            in_spreads = False
            moves = []
            top_spread = None

            for i, line in enumerate(lines):
                if line.startswith('+----------------------------------------+'):
                    if i + 2 < len(lines) and lines[i+2].startswith('+----------------------------------------+'):
                        if current_species and len(meta_list) < 30:
                            meta_list.append({"species": current_species, "moves": moves[:10], "spread": top_spread})
                            if len(meta_list) >= 30:
                                break
                                
                        current_species = lines[i+1].replace('|', '').strip()
                        moves = []
                        top_spread = None
                        in_moves = False
                        in_spreads = False
                        continue
                        
                if '| Moves ' in line:
                    in_moves = True
                    in_spreads = False
                    continue
                    
                if '| Spreads ' in line:
                    in_spreads = True
                    in_moves = False
                    continue
                    
                if in_spreads:
                    if line.startswith('+----------------------------------------+'):
                        in_spreads = False
                        continue
                        
                    spread_match = re.match(r'\|\s+([A-Za-z]+):(\d+)/(\d+)/(\d+)/(\d+)/(\d+)/(\d+)\s+(\d+\.\d+)%', line)
                    if spread_match and not top_spread:
                        top_spread = {
                            "nature": spread_match.group(1),
                            "evs": {
                                "HP": int(spread_match.group(2)),
                                "Atk": int(spread_match.group(3)),
                                "Def": int(spread_match.group(4)),
                                "SpA": int(spread_match.group(5)),
                                "SpD": int(spread_match.group(6)),
                                "Spe": int(spread_match.group(7))
                            }
                        }
                    
                if in_moves:
                    if line.startswith('+----------------------------------------+'):
                        in_moves = False
                        continue
                        
                    move_match = re.match(r'\|\s+([a-zA-Z0-9 -]+?)\s+(\d+\.\d+)%', line)
                    if move_match:
                        # PokeAPI expects spaces to be dashes (e.g. 'sucker-punch')
                        m_name = move_match.group(1).strip().lower().replace(" ", "-")
                        usage_pct = float(move_match.group(2))
                        if m_name and m_name != 'other' and usage_pct >= 25.0:
                            moves.append(m_name)

            if current_species and len(meta_list) < 30:
                meta_list.append({"species": current_species, "moves": moves[:10], "spread": top_spread})
                
            
            if not is_exact:
                return meta_list, f"Could not find Smogon usage stats for {regulation_name}. Displaying closest available data: {best_file.replace('.txt.gz', '')}"
            return meta_list, None
                
        print(f"Could not find regulation {regulation_name} ({shortcode}) or any fallback in recent Smogon stats.")
        return fallback_meta(), 'Smogon stats API is currently unreachable or has no data. Falling back to local offline snapshot.'
        
    except Exception as e:
        print(f"Failed to fetch meta: {e}")
        return fallback_meta(), 'Smogon stats API is currently unreachable or has no data. Falling back to local offline snapshot.'

def fallback_meta():
    return [{"species": p, "moves": []} for p in ['Kingambit', 'Incineroar', 'Garchomp', 'Basculegion', 'Sneasler', 'Charizard-Mega-Y', 'Sinistcha', 'Whimsicott', 'Farigiraf', 'Sylveon', 'Floette-Mega', 'Staraptor-Mega', 'Delphox-Mega', 'Raichu-Mega-Y', 'Blastoise-Mega', 'Archaludon', 'Venusaur', 'Pelipper', 'Froslass-Mega', 'Aerodactyl-Mega', 'Gholdengo', 'Swampert-Mega', 'Grimmsnarl', 'Ninetales-Alola', 'Gengar-Mega', 'Milotic', 'Arcanine-Hisui', 'Maushold', 'Dragonite-Mega', 'Scovillain-Mega']]

TYPE_COLORS = {
    "normal": "#e0e0e0", "fire": "#EE8130", "water": "#6390F0", "electric": "#F7D02C",
    "grass": "#7AC74C", "ice": "#96D9D6", "fighting": "#C22E28", "poison": "#A33EA1",
    "ground": "#E2BF65", "flying": "#A98FF3", "psychic": "#F95587", "bug": "#A6B91A",
    "rock": "#B6A136", "ghost": "#735797", "dragon": "#6F35FC", "dark": "#705746",
    "steel": "#B7B7CE", "fairy": "#D685AD"
}

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
    top_meta, _ = fetch_top_meta_pokemon(regulation_name)
    threats = []
    
    # Pre-calculate team types and abilities
    team_data = []
    for p in team.pokemons:
        data = get_pokemon_data(p.species)
        if data:
            abilities = [p.ability.lower().replace(" ", "").replace("-", "")] if p.ability else []
            if "-mega" in p.species.lower():
                base_species = p.species.lower().split("-mega")[0]
                base_data = get_pokemon_data(base_species)
                if base_data:
                    for ba in base_data.get("abilities", []):
                        abilities.append(ba.lower().replace(" ", "").replace("-", ""))
                        
            team_data.append({
                "species": p.species,
                "types": data["types"],
                "moves": [m.lower().replace(" ", "-") for m in p.moves],
                "abilities": list(set(abilities))
            })
            
    team_abilities = [a for d in team_data for a in d["abilities"]]

    threats = []
    
    for meta_mon in top_meta:
        meta_species = meta_mon["species"]
        sanitized_species = meta_species.lower().replace(" ", "-").replace("'", "").replace(".", "")
        meta_data = get_pokemon_data(sanitized_species)
        if not meta_data: continue
        
        meta_types = meta_data["types"]
        meta_abilities = [a.replace("-", "") for a in meta_data.get("abilities", [])]
        meta_moves = meta_mon.get("moves", [])
        
        # Get top 4 damaging move types for coverage
        meta_coverage = []
        for move in meta_moves:
            dmg_class = get_move_damage_class(move)
            if dmg_class in ["physical", "special"]:
                m_type = get_move_type(move, ignore_status=True, ability=meta_data.get("Ability", ""))
                if m_type and not any(t == m_type for m, t in meta_coverage):
                    meta_coverage.append((move, m_type))
            if len(meta_coverage) >= 4:
                break
                
        if not meta_coverage:
            # Fallback to STAB if no damaging moves found
            meta_coverage = [("STAB", t) for t in meta_types]
            
        hits_team_se = []
        team_hits_se = []
        threat_score = 0
        
        BOOST_ABILITIES = {
            "grassysurge": "Grass",
            "psychicsurge": "Psychic",
            "electricsurge": "Electric",
            "drizzle": "Water",
            "drought": "Fire",
            "orichalcumpulse": "Fire",
            "hadronengine": "Electric"
        }
        
        for t_mon in team_data:
            # Can meta hit team mon SE?
            max_meta_mult = 1.0
            best_move = None
            best_type = None
            for m_name, mt in meta_coverage:
                mult = get_multiplier(mt.lower(), [t.lower() for t in t_mon["types"]])
                if mult > max_meta_mult:
                    max_meta_mult = mult
                    best_move = m_name
                    best_type = mt
            
            if max_meta_mult >= 4.0:
                hits_team_se.append((t_mon["species"], best_move, best_type))
                threat_score += 2
            elif max_meta_mult >= 2.0:
                hits_team_se.append((t_mon["species"], best_move, best_type))
                threat_score += 1
                
            if max_meta_mult >= 2.0 and best_type:
                for ab, boost_type in BOOST_ABILITIES.items():
                    if ab in meta_abilities and best_type == boost_type:
                        threat_score += 1
                        break
                
            # Can team mon hit meta SE?
            max_team_mult = 1.0
            best_team_type = None
            move_types = []
            if t_mon.get("moves"):
                for m in t_mon["moves"]:
                    if get_move_damage_class(m) in ["physical", "special"]:
                        m_type = get_move_type(m, ignore_status=True, ability=t_mon.get("ability", ""))
                        if m_type:
                            move_types.append(m_type)
                            
            if not move_types:
                move_types = t_mon["types"] # Fallback to STAB if no attacking moves
                
            for tt in move_types:
                mult = get_multiplier(tt.lower(), [t.lower() for t in meta_types])
                if mult > max_team_mult:
                    max_team_mult = mult
                    best_team_type = tt
                    
            if max_team_mult >= 4.0:
                team_hits_se.append(t_mon["species"])
                threat_score -= 100 # Negate threat entirely
            elif max_team_mult >= 2.0:
                team_hits_se.append(t_mon["species"])
                threat_score -= 1
                
                if best_team_type:
                    for ab, boost_type in BOOST_ABILITIES.items():
                        if ab in t_mon["abilities"] and best_team_type == boost_type:
                            threat_score -= 1
                            break
                
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
            
        if is_ability_threat:
            threat_score += 3
            
        # Weather disruption penalization
        is_weather_mitigated = False
        WEATHER_SETTERS = {"drizzle", "drought", "sandstream", "snowwarning", "orichalcumpulse", "desolateland", "primordialsea"}
        team_weather_setters = set(team_abilities).intersection(WEATHER_SETTERS)
        meta_weather_setters = set(meta_abilities).intersection(WEATHER_SETTERS)
        
        if team_weather_setters and meta_weather_setters and team_weather_setters != meta_weather_setters:
            is_weather_mitigated = True
            
        WEATHER_WEAKENS = {
            "drizzle": "Fire",
            "primordialsea": "Fire",
            "drought": "Water",
            "desolateland": "Water",
            "orichalcumpulse": "Water"
        }
        for tw in team_weather_setters:
            if tw in WEATHER_WEAKENS:
                weakened_type = WEATHER_WEAKENS[tw]
                if any(mt.capitalize() == weakened_type or mt == weakened_type for m_name, mt in meta_coverage):
                    is_weather_mitigated = True
                    break
                    
        if is_weather_mitigated:
            threat_score -= 2
                
        # Ensure uniqueness
        hits_team_se = list(set(hits_team_se))
        team_hits_se = list(set(team_hits_se))
        
        if threat_score >= 2:
            # Construct explanation
            explanation = ""
            if hits_team_se:
                hit_strs = []
                for spec, m_name, m_type in hits_team_se:
                    color = TYPE_COLORS.get(m_type.lower(), "#ffffff")
                    m_display = m_name.replace('-', ' ').title() if m_name != "STAB" else f"STAB {m_type.title()}"
                    hit_strs.append(f"{spec} (<span style='color: {color}; font-weight: bold;'>{m_display}</span>)")
                    
                explanation += f"Hits {', '.join(hit_strs)} for Super Effective damage. "
                if not team_hits_se:
                    explanation += "No one on your team can hit it for SE damage! "
                else:
                    explanation += f"Your {', '.join(team_hits_se)} can hit it for SE damage. "
            else:
                if not team_hits_se:
                    explanation += "No one on your team can hit it for SE damage! "
                else:
                    explanation += f"Your {', '.join(team_hits_se)} can hit it for SE damage. "
            
            if is_ability_threat:
                explanation += " " + ability_threat_msg
                
            threats.append({
                "species": meta_species,
                "sprite": meta_data.get("sprite", ""),
                "hits_team": [h[0] for h in hits_team_se],
                "team_hits_it": team_hits_se,
                "score": threat_score,
                "explanation": explanation.strip()
            })
            
    threats.sort(key=lambda x: x["score"], reverse=True)
    return threats


@st.cache_data(ttl=86400)
def get_meta_avg_stats(regulation_name: str):
    from src.pokeapi import calculate_stat
    from src.pokeapi import get_nature_multiplier
    meta_list, _ = fetch_top_meta_pokemon(regulation_name)
    m_hps, m_atks, m_defs, m_spas, m_spds, m_spes = [], [], [], [], [], []
    
    for m in meta_list:
        m_data = get_pokemon_data(m['species'])
        m_base = m_data['stats']
        m_spread = m.get('spread')
        if not m_spread:
            m_spread = {'nature': 'Serious', 'evs': {'HP':0, 'Atk':0, 'Def':0, 'SpA':0, 'SpD':0, 'Spe':0}}
            
        m_actual = {}
        for stat_name in ['HP', 'Atk', 'Def', 'SpA', 'SpD', 'Spe']:
            is_hp = (stat_name == 'HP')
            b = m_base.get(stat_name, 100)
            ev = m_spread['evs'].get(stat_name, 0)
            nature_mult = get_nature_multiplier(m_spread['nature'], stat_name)
            m_actual[stat_name] = calculate_stat(b, ev, 31, 50, is_hp, nature_mult)
            
        m_hps.append(m_actual['HP'])
        m_defs.append(m_actual['Def'])
        m_spds.append(m_actual['SpD'])
        m_spes.append(m_actual['Spe'])
        
        phys_moves = sum(1 for move in m.get('moves', []) if get_move_damage_class(move) == 'physical')
        spec_moves = sum(1 for move in m.get('moves', []) if get_move_damage_class(move) == 'special')
        if phys_moves == 0 and spec_moves == 0:
            if m_base.get('Atk', 0) > m_base.get('SpA', 0):
                phys_moves = 1
            else:
                spec_moves = 1
                
        if phys_moves > 0:
            m_atks.append(m_actual['Atk'])
        if spec_moves > 0:
            m_spas.append(m_actual['SpA'])

    return {
        'HP': int(sum(m_hps)/len(m_hps)) if m_hps else 100,
        'Atk': int(sum(m_atks)/len(m_atks)) if m_atks else 100,
        'Def': int(sum(m_defs)/len(m_defs)) if m_defs else 100,
        'Spe': int(sum(m_spes)/len(m_spes)) if m_spes else 100,
        'SpD': int(sum(m_spds)/len(m_spds)) if m_spds else 100,
        'SpA': int(sum(m_spas)/len(m_spas)) if m_spas else 100,
    }
