from src.synergy import calculate_defensive_synergy, TYPE_EFFECTIVENESS
from src.pokeapi import is_spread_damage, get_move_type


def calculate_lead_synergy(p1, p2):
    score = 0
    reasons = []
    
    # Extract moves and stats
    p1_moves = p1.get('Moves', [])
    p2_moves = p2.get('Moves', [])
    p1_types = p1.get('Types', [])
    p2_types = p2.get('Types', [])
    p1_ability = p1.get('Ability', '')
    p2_ability = p2.get('Ability', '')
    
    p1_offense = max(p1.get('Atk', 0), p1.get('SpA', 0))
    p2_offense = max(p2.get('Atk', 0), p2.get('SpA', 0))
    
    # Check Support
    support_moves = {"Fake Out", "Parting Shot", "Will-O-Wisp", "Snarl", "Taunt", "Spore", "Yawn", "Reflect", "Light Screen", "Aurora Veil", "Follow Me", "Rage Powder", "Pollen Puff", "Helping Hand", "Tailwind", "Icy Wind", "Electroweb", "Thunder Wave", "Trick Room", "Roar", "Whirlwind", "Clear Smog", "Haze"}
    p1_support_count = sum(1 for m in p1_moves if m in support_moves)
    p2_support_count = sum(1 for m in p2_moves if m in support_moves)
    
    p1_fake_out = "Fake Out" in p1_moves
    p2_fake_out = "Fake Out" in p2_moves
    
    setup_moves = {"Swords Dance", "Nasty Plot", "Dragon Dance", "Calm Mind", "Bulk Up", "Iron Defense", "Quiver Dance", "Coil"}
    p1_setup = any(m in setup_moves for m in p1_moves)
    p2_setup = any(m in setup_moves for m in p2_moves)
    
    speed_control_moves = {"Tailwind", "Icy Wind", "Trick Room", "Electroweb", "Thunder Wave"}
    p1_speed_control = any(m in speed_control_moves for m in p1_moves)
    p2_speed_control = any(m in speed_control_moves for m in p2_moves)
    
    redirect_moves = {"Follow Me", "Rage Powder"}
    p1_redirect = any(m in redirect_moves for m in p1_moves)
    p2_redirect = any(m in redirect_moves for m in p2_moves)
    
    # Positive Synergy
    # Fake Out
    if p1_fake_out and p2_setup:
        score += 3
        reasons.append("Fake Out + Setup (+3)")
    elif p1_fake_out and p2_speed_control:
        score += 2
        reasons.append("Fake Out + Speed Control (+2)")
    elif p1_fake_out and p2_offense > 100 and not p2_fake_out and p2_support_count <= 1:
        score += 2
        reasons.append("Fake Out + Attacker (+2)")
        
    if p2_fake_out and p1_setup:
        score += 3
        reasons.append("Fake Out + Setup (+3)")
    elif p2_fake_out and p1_speed_control:
        score += 2
        reasons.append("Fake Out + Speed Control (+2)")
    elif p2_fake_out and p1_offense > 100 and not p1_fake_out and p1_support_count <= 1:
        score += 2
        reasons.append("Fake Out + Attacker (+2)")
        
    # Redirection
    if p1_redirect and p2_setup:
        score += 3
        reasons.append("Redirection + Setup (+3)")
    elif p1_redirect and p2_offense > 100 and p2_support_count <= 1:
        score += 2
        reasons.append("Redirection + Attacker (+2)")
        
    if p2_redirect and p1_setup:
        score += 3
        reasons.append("Redirection + Setup (+3)")
    elif p2_redirect and p1_offense > 100 and p1_support_count <= 1:
        score += 2
        reasons.append("Redirection + Attacker (+2)")
        
    # Spread Damage Check
    p1_spread = False
    p2_spread = False
    p1_spread_hits_ally = []
    p2_spread_hits_ally = []
    
    for m in p1_moves:
        target = is_spread_damage(m)
        if target:
            p1_spread = True
            if target == 'all-other-pokemon':
                p1_spread_hits_ally.append(m)
                
    for m in p2_moves:
        target = is_spread_damage(m)
        if target:
            p2_spread = True
            if target == 'all-other-pokemon':
                p2_spread_hits_ally.append(m)

    # Speed Control + Attacker / Spread Damage
    speed_bonus_applied = False
    spread_bonus_applied = False
    if p1_speed_control and not p1_fake_out:
        if p2_spread and p2_offense > 100 and p2_support_count <= 1:
            score += 4
            reasons.append("Speed Control + Spread Damage (+4)")
            speed_bonus_applied = True
            spread_bonus_applied = True
        elif p2_offense > 100 and p2_support_count <= 1:
            score += 2
            reasons.append("Speed Control + Attacker (+2)")
            speed_bonus_applied = True
            
    if p2_speed_control and not p2_fake_out and not speed_bonus_applied:
        if p1_spread and p1_offense > 100 and p1_support_count <= 1:
            score += 4
            reasons.append("Speed Control + Spread Damage (+4)")
            spread_bonus_applied = True
        elif p1_offense > 100 and p1_support_count <= 1:
            score += 2
            reasons.append("Speed Control + Attacker (+2)")
        
    # Weather/Terrain
    weather_setters = {"Drizzle": "Rain", "Drought": "Sun", "Sand Stream": "Sand", "Snow Warning": "Snow", "Orichalcum Pulse": "Sun", "Hadron Engine": "Electric"}
    p1_weather = weather_setters.get(p1_ability)
    p2_weather = weather_setters.get(p2_ability)
    
    weather_abusers = {"Swift Swim": "Rain", "Chlorophyll": "Sun", "Protosynthesis": "Sun", "Sand Rush": "Sand", "Slush Rush": "Snow", "Solar Power": "Sun", "Quark Drive": "Electric"}
    p1_abuser = weather_abusers.get(p1_ability)
    p2_abuser = weather_abusers.get(p2_ability)
    
    if (p1_weather and p2_abuser == p1_weather) or (p2_weather and p1_abuser == p2_weather):
        score += 4
        reasons.append("Weather/Terrain Ability Synergy (+4)")
        
    if p1_weather == "Rain" and "Water" in p2_types:
        score += 1
        reasons.append("Rain + Water Type (+1)")
    if p2_weather == "Rain" and "Water" in p1_types:
        score += 1
        reasons.append("Rain + Water Type (+1)")
    if p1_weather == "Sun" and "Fire" in p2_types:
        score += 1
        reasons.append("Sun + Fire Type (+1)")
    if p2_weather == "Sun" and "Fire" in p1_types:
        score += 1
        reasons.append("Sun + Fire Type (+1)")
        
    # Commander
    if (p1.get('Pokemon') == 'Dondozo' and p2.get('Pokemon') == 'Tatsugiri') or (p2.get('Pokemon') == 'Dondozo' and p1.get('Pokemon') == 'Tatsugiri'):
        score += 5
        reasons.append("Commander Core (+5)")
        
    # Intimidate
    support_abilities = {"Intimidate", "Friend Guard", "Vessel of Ruin", "Tablets of Ruin", "Fluffy", "Fur Coat"}
    if p1_ability in support_abilities:
        score += 1
        reasons.append(f"{p1_ability} Support (+1)")
    if p2_ability in support_abilities:
        score += 1
        reasons.append(f"{p2_ability} Support (+1)")
        
    # Spread Damage Base Points
    if (p1_spread or p2_spread) and not spread_bonus_applied:
        score += 1
        reasons.append("Spread Damage (+1)")

    # Ally immunity check
    def is_immune(move, defender_types, defender_ability):
        move_type = get_move_type(move)
        if not move_type: return False
        move_type = move_type.capitalize()
        
        # Check type immunity
        for dt in defender_types:
            dt_cap = dt.capitalize()
            if dt_cap in TYPE_EFFECTIVENESS:
                if move_type in TYPE_EFFECTIVENESS[dt_cap]["immune"]:
                    return True
            
        imm = {
            "Water": ["Water Absorb", "Storm Drain", "Dry Skin"],
            "Electric": ["Volt Absorb", "Lightning Rod", "Motor Drive"],
            "Ground": ["Levitate", "Earth Eater"],
            "Fire": ["Flash Fire", "Well-Baked Body"],
            "Grass": ["Sap Sipper"]
        }
        if move_type in imm and defender_ability in imm[move_type]:
            return True
            
        if defender_ability == "Telepathy":
            return True
            
        return False
        
    for m in p1_spread_hits_ally:
        if not is_immune(m, p2_types, p2_ability):
            score -= 2
            reasons.append(f"{m.title().replace('-', ' ')} damages partner (-2)")
            
    for m in p2_spread_hits_ally:
        if not is_immune(m, p1_types, p1_ability):
            score -= 2
            reasons.append(f"{m.title().replace('-', ' ')} damages partner (-2)")

    # Negative Synergy & Type Coverage
    p1_def = calculate_defensive_synergy(p1_types)
    p2_def = calculate_defensive_synergy(p2_types)
    
    p1_weaknesses = [t for t, mult in p1_def.items() if mult > 1.0]
    p2_weaknesses = [t for t, mult in p2_def.items() if mult > 1.0]
    
    shared_weak = set(p1_weaknesses).intersection(set(p2_weaknesses))
    if shared_weak:
        penalty = len(shared_weak) * 1.5
        score -= penalty
        reasons.append(f"Shared Weaknesses: {', '.join(shared_weak)} (-{penalty})")
        
    # Positive Type Coverage (P1 resists P2's weakness and vice versa)
    covered = 0
    covered_types = []
    for w in p1_weaknesses:
        if p2_def.get(w, 1.0) < 1.0:
            covered += 1
            covered_types.append(w)
    for w in p2_weaknesses:
        if p1_def.get(w, 1.0) < 1.0:
            covered += 1
            covered_types.append(w)
            
    if covered > 0:
        score += covered * 1.0
        # reasons.append(f"Type Coverage Synergy: {', '.join(set(covered_types))} (+{covered})")
        reasons.append(f"Type Synergy Coverage (+{covered})")
        

    if p1_fake_out and p2_fake_out:
        score -= 2
        reasons.append("Redundant Double Fake Out (-2)")
        
    # Double offensive pressure
    if p1_offense > 100 and p2_offense > 100 and p1_support_count <= 1 and p2_support_count <= 1 and not p1_fake_out and not p2_fake_out:
        score += 2
        reasons.append("High Double Offensive Pressure (+2)")

    # Heavily penalize double support without setup/offensive presence

    if p1_support_count >= 2 and p2_support_count >= 2:
        score -= 5
        reasons.append("Extreme Double Support / Passive Lead (-5)")
    elif p1_support_count >= 1 and p2_support_count >= 1 and not p1_setup and not p2_setup:
        score -= 3
        reasons.append("Double Support / Low Offensive Pressure (-3)")

    if score >= 5.0:
        grade = 'S'
    elif score >= 2.5:
        grade = 'A'
    elif score >= 0.5:
        grade = 'B'
    else:
        grade = 'C'
        
    return grade, reasons


def evaluate_all_leads(team_data):
    n = len(team_data)
    matrix = [[('-', []) for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                matrix[i][j] = calculate_lead_synergy(team_data[i], team_data[j])
    return matrix

def build_leads_matrix_html(team_data, leads_matrix):
    n = len(team_data)
    
    html = '''
    <style>
    .lead-tooltip-container {
        position: relative;
        cursor: help;
    }
    .lead-tooltip-container .lead-tooltip-text {
        visibility: hidden;
        background-color: #1a1c23;
        color: #e0e0e0;
        text-align: left;
        border-radius: 8px;
        padding: 10px 14px;
        position: absolute;
        z-index: 1000;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        margin-bottom: 8px;
        width: max-content;
        max-width: 240px;
        opacity: 0;
        transition: opacity 0.2s, transform 0.2s;
        border: 1px solid rgba(255,255,255,0.15);
        box-shadow: 0 8px 24px rgba(0,0,0,0.6);
        font-size: 0.75rem;
        font-weight: normal;
        line-height: 1.4;
        pointer-events: none;
    }
    .lead-tooltip-container:hover .lead-tooltip-text {
        visibility: visible;
        opacity: 1;
        transform: translateX(-50%) translateY(-2px);
    }
    .lead-tooltip-text ul {
        margin: 0;
        padding-left: 20px;
        margin-top: 6px;
    }
    .lead-tooltip-text li {
        margin-bottom: 4px;
    }
    </style>
    '''
    
    html += "<div style='display: flex; gap: 40px; align-items: flex-start; margin-top: 20px;'>"
    html += "<div style='border-radius: 12px; overflow: hidden;'>"
    html += "<table style='border-collapse: collapse; text-align: center; font-size: 1.3em; font-weight: bold; background-color: rgba(255,255,255,0.02);'>"
    
    html += "<tr><td style='border: none; background-color: transparent;'></td>"
    for j in range(n):
        html += f"<td style='padding: 5px; border: none; background-color: transparent;'><img src='{team_data[j].get('Sprite', '')}' width='60' title='{team_data[j].get('Pokémon', '')}'></td>"
    html += "</tr>"
    
    for i in range(n):
        html += "<tr>"
        html += f"<td style='padding: 5px; border: none; background-color: transparent;'><img src='{team_data[i].get('Sprite', '')}' width='60' title='{team_data[i].get('Pokémon', '')}'></td>"
        for j in range(n):
            if j >= i:
                html += "<td style='background-color: #8c8c8c; border: 1px solid rgba(0,0,0,0.1); width: 75px; height: 75px;'></td>"
            else:
                grade, reasons = leads_matrix[i][j]
                
                # Format reasons into an HTML list
                reasons_html = "<ul>" + "".join(f"<li>{r}</li>" for r in reasons) + "</ul>" if reasons else "<div style='margin-top: 5px; opacity: 0.7;'>No significant synergies or penalties.</div>"
                
                # Adjust tooltip placement for edge columns to prevent clipping
                tooltip_style = ""
                if j == 0:
                    tooltip_style = "left: 10px; transform: none;"
                elif j == n - 2:
                    tooltip_style = "right: 10px; left: auto; transform: none;"
                    
                html += f"<td class='lead-tooltip-container' style='padding: 10px; border: 1px solid rgba(255,255,255,0.1); width: 75px; height: 75px; color: #e6e6e6; background-color: rgba(255,255,255,0.05);'>"
                html += f"{grade}"
                html += f"<div class='lead-tooltip-text' style='{tooltip_style}'><strong>Grade {grade} Criteria:</strong>{reasons_html}</div>"
                html += "</td>"
        html += "</tr>"
    
    html += "</table></div>"
    html += '''
    <div style='display: flex; flex-direction: column; justify-content: center; gap: 15px; font-size: 1.1em; padding-top: 50px;'>
        <div style='border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 5px;'><span style='font-weight: bold; margin-right: 15px;'>S</span> Strong and consistent <span style='font-size: 0.8em; color: #a0a0a0; margin-left: 5px;'>(4+ points)</span></div>
        <div style='border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 5px;'><span style='font-weight: bold; margin-right: 15px;'>A</span> Strong and somewhat consistent <span style='font-size: 0.8em; color: #a0a0a0; margin-left: 5px;'>(2+ points)</span></div>
        <div style='border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 5px;'><span style='font-weight: bold; margin-right: 15px;'>B</span> Weak or not very consistent <span style='font-size: 0.8em; color: #a0a0a0; margin-left: 5px;'>(0+ points)</span></div>
        <div style='border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 5px;'><span style='font-weight: bold; margin-right: 15px;'>C</span> Niche or not usable <span style='font-size: 0.8em; color: #a0a0a0; margin-left: 5px;'>(< 0 points)</span></div>
    </div>
    </div>
    '''
    return html
