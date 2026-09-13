from typing import List, Dict

TYPE_EFFECTIVENESS = {
    "Normal":   {"weak": ["Fighting"], "resist": [], "immune": ["Ghost"]},
    "Fire":     {"weak": ["Water", "Ground", "Rock"], "resist": ["Fire", "Grass", "Ice", "Bug", "Steel", "Fairy"], "immune": []},
    "Water":    {"weak": ["Electric", "Grass"], "resist": ["Fire", "Water", "Ice", "Steel"], "immune": []},
    "Electric": {"weak": ["Ground"], "resist": ["Electric", "Flying", "Steel"], "immune": []},
    "Grass":    {"weak": ["Fire", "Ice", "Poison", "Flying", "Bug"], "resist": ["Water", "Electric", "Grass", "Ground"], "immune": []},
    "Ice":      {"weak": ["Fire", "Fighting", "Rock", "Steel"], "resist": ["Ice"], "immune": []},
    "Fighting": {"weak": ["Flying", "Psychic", "Fairy"], "resist": ["Bug", "Rock", "Dark"], "immune": []},
    "Poison":   {"weak": ["Ground", "Psychic"], "resist": ["Grass", "Fighting", "Poison", "Bug", "Fairy"], "immune": []},
    "Ground":   {"weak": ["Water", "Grass", "Ice"], "resist": ["Poison", "Rock"], "immune": ["Electric"]},
    "Flying":   {"weak": ["Electric", "Ice", "Rock"], "resist": ["Grass", "Fighting", "Bug"], "immune": ["Ground"]},
    "Psychic":  {"weak": ["Bug", "Ghost", "Dark"], "resist": ["Fighting", "Psychic"], "immune": []},
    "Bug":      {"weak": ["Fire", "Flying", "Rock"], "resist": ["Grass", "Fighting", "Ground"], "immune": []},
    "Rock":     {"weak": ["Water", "Grass", "Fighting", "Ground", "Steel"], "resist": ["Normal", "Fire", "Poison", "Flying"], "immune": []},
    "Ghost":    {"weak": ["Ghost", "Dark"], "resist": ["Poison", "Bug"], "immune": ["Normal", "Fighting"]},
    "Dragon":   {"weak": ["Ice", "Dragon", "Fairy"], "resist": ["Fire", "Water", "Electric", "Grass"], "immune": []},
    "Dark":     {"weak": ["Fighting", "Bug", "Fairy"], "resist": ["Ghost", "Dark"], "immune": ["Psychic"]},
    "Steel":    {"weak": ["Fire", "Fighting", "Ground"], "resist": ["Normal", "Grass", "Ice", "Flying", "Psychic", "Bug", "Rock", "Dragon", "Steel", "Fairy"], "immune": ["Poison"]},
    "Fairy":    {"weak": ["Poison", "Steel"], "resist": ["Fighting", "Bug", "Dark"], "immune": ["Dragon"]},
}

ALL_TYPES = list(TYPE_EFFECTIVENESS.keys())

def calculate_defensive_synergy(types: List[str]) -> Dict[str, float]:
    """Calculates defensive multipliers against all attacking types based on the pokemon's types."""
    multipliers = {t: 1.0 for t in ALL_TYPES}
    
    for t in types:
        if t not in TYPE_EFFECTIVENESS: continue
        for weak in TYPE_EFFECTIVENESS[t]["weak"]:
            multipliers[weak] *= 2.0
        for resist in TYPE_EFFECTIVENESS[t]["resist"]:
            multipliers[resist] *= 0.5
        for immune in TYPE_EFFECTIVENESS[t]["immune"]:
            multipliers[immune] *= 0.0
            
    return multipliers
    
def calculate_offensive_synergy(move_types: List[str]) -> Dict[str, float]:
    """Calculates best offensive multipliers against all defending types based on a pokemon's move types."""
    multipliers = {t: 0.0 for t in ALL_TYPES}
    if not move_types:
        return multipliers
        
    for def_type in ALL_TYPES:
        best_mult = 0.0
        for m_type in move_types:
            if m_type not in TYPE_EFFECTIVENESS: continue
            
            # Default is 1x
            current_mult = 1.0
            
            # Check def_type's weaknesses/resistances to the move_type
            if m_type in TYPE_EFFECTIVENESS[def_type]["weak"]:
                current_mult = 2.0
            elif m_type in TYPE_EFFECTIVENESS[def_type]["resist"]:
                current_mult = 0.5
            elif m_type in TYPE_EFFECTIVENESS[def_type]["immune"]:
                current_mult = 0.0
                
            if current_mult > best_mult:
                best_mult = current_mult
                
        multipliers[def_type] = best_mult
        
    return multipliers
