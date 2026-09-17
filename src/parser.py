import re
from typing import List, Dict
from src.models import Pokemon, Team

def parse_showdown_paste(paste_text: str) -> Team:
    """Parses a Pokemon Showdown format paste into a Team object."""
    # Normalize Windows CRLF line endings to LF before splitting
    normalized_text = paste_text.replace("\r\n", "\n")
    blocks = normalized_text.strip().split("\n\n")
    team = Team()
    
    for block in blocks:
        if not block.strip():
            continue
        
        lines = block.strip().split('\n')
        if not lines:
            continue
            
        pokemon = Pokemon(species="")
        
        # Line 1: Species (Gender) @ Item or just Species
        first_line = lines[0].strip()
        
        # Extract Item
        if '@' in first_line:
            name_part, item = first_line.split('@', 1)
            pokemon.item = item.strip()
        else:
            name_part = first_line
            
        name_part = name_part.strip()
        
        # Extract Gender
        gender_match = re.search(r'\((M|F)\)', name_part)
        if gender_match:
            pokemon.gender = gender_match.group(1)
            name_part = name_part.replace(gender_match.group(0), '').strip()
            
        # Species is whatever is left
        pokemon.species = name_part
        
        # Parse remaining lines
        for line in lines[1:]:
            line = line.strip()
            if line.startswith('Ability:'):
                pokemon.ability = line.replace('Ability:', '').strip()
            elif line.startswith('Level:'):
                pokemon.level = int(line.replace('Level:', '').strip())
            elif line.startswith('Shiny:'):
                pokemon.shiny = line.replace('Shiny:', '').strip().lower() == 'yes'
            elif line.startswith('Tera Type:'):
                pokemon.tera_type = line.replace('Tera Type:', '').strip()
            elif line.startswith('EVs:'):
                ev_str = line.replace('EVs:', '').strip()
                pokemon.evs = _parse_stats_line(ev_str, default=0)
            elif line.startswith('IVs:'):
                iv_str = line.replace('IVs:', '').strip()
                pokemon.ivs = _parse_stats_line(iv_str, default=31)
            elif line.endswith(' Nature'):
                pokemon.nature = line.replace(' Nature', '').strip()
            elif line.startswith('-'):
                pokemon.moves.append(line[1:].strip())
                
        team.pokemons.append(pokemon)
        
    return team

def _parse_stats_line(stats_str: str, default: int) -> Dict[str, int]:
    stats = {"HP": default, "Atk": default, "Def": default, "SpA": default, "SpD": default, "Spe": default}
    parts = stats_str.split('/')
    for part in parts:
        part = part.strip()
        if not part: continue
        val, stat = part.split(' ', 1)
        stats[stat.strip()] = int(val.strip())
    return stats
