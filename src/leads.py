from src.synergy import calculate_defensive_synergy, TYPE_EFFECTIVENESS

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
    support_moves = {"Fake Out", "Parting Shot", "Will-O-Wisp", "Snarl", "Taunt", "Spore", "Yawn", "Reflect", "Light Screen", "Aurora Veil", "Follow Me", "Rage Powder", "Pollen Puff", "Helping Hand"}
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
    elif p1_fake_out and p2_offense > 100 and not p2_fake_out:
        score += 2
        reasons.append("Fake Out + Attacker (+2)")
        
    if p2_fake_out and p1_setup:
        score += 3
        reasons.append("Fake Out + Setup (+3)")
    elif p2_fake_out and p1_speed_control:
        score += 2
        reasons.append("Fake Out + Speed Control (+2)")
    elif p2_fake_out and p1_offense > 100 and not p1_fake_out:
        score += 2
        reasons.append("Fake Out + Attacker (+2)")
        
    # Redirection
    if p1_redirect and p2_setup:
        score += 3
        reasons.append("Redirection + Setup (+3)")
    elif p1_redirect and p2_offense > 100:
        score += 2
        reasons.append("Redirection + Attacker (+2)")
        
    if p2_redirect and p1_setup:
        score += 3
        reasons.append("Redirection + Setup (+3)")
    elif p2_redirect and p1_offense > 100:
        score += 2
        reasons.append("Redirection + Attacker (+2)")
        
    # Spread Damage Check
    common_spread = {"Earthquake", "Rock Slide", "Dazzling Gleam", "Heat Wave", "Snarl", "Icy Wind", "Eruption", "Water Spout", "Make It Rain", "Hyper Voice", "Muddy Water", "Expand Force", "Bleakwind Storm", "Wildbolt Storm", "Sandsear Storm"}
    p1_spread = any(m in common_spread for m in p1_moves)
    p2_spread = any(m in common_spread for m in p2_moves)

    # Speed Control + Attacker / Spread Damage
    speed_bonus_applied = False
    if p1_speed_control and not p1_fake_out:
        if p2_spread and p2_offense > 100:
            score += 4
            reasons.append("Speed Control + Spread Damage (+4)")
            speed_bonus_applied = True
        elif p2_offense > 100:
            score += 2
            reasons.append("Speed Control + Attacker (+2)")
            speed_bonus_applied = True
            
    if p2_speed_control and not p2_fake_out and not speed_bonus_applied:
        if p1_spread and p1_offense > 100:
            score += 4
            reasons.append("Speed Control + Spread Damage (+4)")
        elif p1_offense > 100:
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
    if (p1.get('Pokémon') == 'Dondozo' and p2.get('Pokémon') == 'Tatsugiri') or (p2.get('Pokémon') == 'Dondozo' and p1.get('Pokémon') == 'Tatsugiri'):
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
    if p1_spread or p2_spread:
        score += 1
        reasons.append("Spread Damage (+1)")

    # Negative Synergy
    def get_weak(types):
        weak_to = set()
        for attack_type, defense_data in TYPE_EFFECTIVENESS.items():
            mult = 1.0
            for t in types:
                if t in defense_data:
                    mult *= defense_data[t]
            if mult > 1.0:
                weak_to.add(attack_type)
        return weak_to
        
    p1_weak = get_weak(p1_types)
    p2_weak = get_weak(p2_types)
    shared_weak = p1_weak.intersection(p2_weak)
    if shared_weak:
        penalty = len(shared_weak) * 1.5
        score -= penalty
        reasons.append(f"Shared Weaknesses: {', '.join(shared_weak)} (-{penalty})")
        
    if p1_fake_out and p2_fake_out:
        score -= 2
        reasons.append("Redundant Double Fake Out (-2)")
        
    if p1_support_count >= 1 and p2_support_count >= 1 and not p1_setup and not p2_setup:
        # Heavily penalize double support if neither sets up
        score -= 3
        reasons.append("Double Support / Low Offensive Pressure (-3)")

    if score >= 4:
        grade = 'S'
    elif score >= 2:
        grade = 'A'
    elif score >= 0:
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
    
    html = "<div style='display: flex; gap: 40px; align-items: flex-start; margin-top: 20px;'>"
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
                reasons_str = "&#10;".join(reasons)
                html += f"<td title='{reasons_str}' style='padding: 10px; border: 1px solid rgba(255,255,255,0.1); width: 75px; height: 75px; color: #e6e6e6; background-color: rgba(255,255,255,0.05); cursor: help;'>{grade}</td>"
        html += "</tr>"
    
    html += "</table></div>"
    html += '''
    <div style='display: flex; flex-direction: column; justify-content: center; gap: 15px; font-size: 1.1em; padding-top: 50px;'>
        <div style='border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 5px;'><span style='font-weight: bold; margin-right: 15px;'>S</span> Strong and consistent</div>
        <div style='border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 5px;'><span style='font-weight: bold; margin-right: 15px;'>A</span> Strong and somewhat consistent</div>
        <div style='border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 5px;'><span style='font-weight: bold; margin-right: 15px;'>B</span> Weak or not very consistent</div>
        <div style='border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 5px;'><span style='font-weight: bold; margin-right: 15px;'>C</span> Niche or not usable</div>
    </div>
    </div>
    '''
    return html
