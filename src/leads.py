from src.synergy import calculate_defensive_synergy, TYPE_EFFECTIVENESS

def calculate_lead_synergy(p1, p2):
    score = 0
    
    # Extract moves and stats
    p1_moves = p1.get('Moves', [])
    p2_moves = p2.get('Moves', [])
    p1_types = p1.get('Types', [])
    p2_types = p2.get('Types', [])
    p1_ability = p1.get('Ability', '')
    p2_ability = p2.get('Ability', '')
    
    p1_offense = max(p1.get('Atk', 0), p1.get('SpA', 0))
    p2_offense = max(p2.get('Atk', 0), p2.get('SpA', 0))
    
    # 1. Fake Out Synergy
    p1_fake_out = "Fake Out" in p1_moves
    p2_fake_out = "Fake Out" in p2_moves
    
    setup_moves = {"Swords Dance", "Nasty Plot", "Dragon Dance", "Calm Mind", "Bulk Up", "Iron Defense", "Quiver Dance", "Coil"}
    p1_setup = any(m in setup_moves for m in p1_moves)
    p2_setup = any(m in setup_moves for m in p2_moves)
    
    speed_control_moves = {"Tailwind", "Icy Wind", "Trick Room", "Electroweb", "Thunder Wave"}
    p1_speed_control = any(m in speed_control_moves for m in p1_moves)
    p2_speed_control = any(m in speed_control_moves for m in p2_moves)
    
    # Redirection
    redirect_moves = {"Follow Me", "Rage Powder"}
    p1_redirect = any(m in redirect_moves for m in p1_moves)
    p2_redirect = any(m in redirect_moves for m in p2_moves)
    
    # Fake Out + Setup / Speed Control / High Offense
    if (p1_fake_out and (p2_setup or p2_speed_control or p2_offense > 110)):
        score += 3
    if (p2_fake_out and (p1_setup or p1_speed_control or p1_offense > 110)):
        score += 3
        
    # Redirection + Setup / Offense
    if (p1_redirect and (p2_setup or p2_offense > 110)):
        score += 3
    if (p2_redirect and (p1_setup or p1_offense > 110)):
        score += 3
        
    # Speed Control + Attacker
    if (p1_speed_control and p2_offense > 100):
        score += 2
    if (p2_speed_control and p1_offense > 100):
        score += 2
        
    # Weather/Terrain Synergy
    weather_setters = {"Drizzle": "Rain", "Drought": "Sun", "Sand Stream": "Sand", "Snow Warning": "Snow", "Orichalcum Pulse": "Sun", "Hadron Engine": "Electric"}
    p1_weather = weather_setters.get(p1_ability)
    p2_weather = weather_setters.get(p2_ability)
    
    weather_abusers = {"Swift Swim": "Rain", "Chlorophyll": "Sun", "Protosynthesis": "Sun", "Sand Rush": "Sand", "Slush Rush": "Snow", "Solar Power": "Sun", "Quark Drive": "Electric"}
    p1_abuser = weather_abusers.get(p1_ability)
    p2_abuser = weather_abusers.get(p2_ability)
    
    if (p1_weather and p2_abuser == p1_weather) or (p2_weather and p1_abuser == p2_weather):
        score += 3
        
    # Weather move typing synergy
    if p1_weather == "Rain" and "Water" in p2_types: score += 1
    if p2_weather == "Rain" and "Water" in p1_types: score += 1
    if p1_weather == "Sun" and "Fire" in p2_types: score += 1
    if p2_weather == "Sun" and "Fire" in p1_types: score += 1
    
    # Commander
    if (p1.get('Pokémon') == 'Dondozo' and p2.get('Pokémon') == 'Tatsugiri') or (p2.get('Pokémon') == 'Dondozo' and p1.get('Pokémon') == 'Tatsugiri'):
        score += 5
    
    # Intimidate / Support Abilities
    support_abilities = {"Intimidate", "Friend Guard", "Vessel of Ruin", "Tablets of Ruin", "Fluffy", "Fur Coat"}
    if p1_ability in support_abilities or p2_ability in support_abilities:
        score += 1
        
    # Shared Weaknesses Penalty
    def get_weaknesses(types):
        weaknesses = set()
        for t in types:
            if t in TYPE_EFFECTIVENESS:
                for target_type, multiplier in TYPE_EFFECTIVENESS[t].items():
                    if multiplier > 1.0:
                        weaknesses.add(target_type)
        return weaknesses
    
    # Use existing TYPE_EFFECTIVENESS which is structured as attacking_type -> defending_type -> multiplier
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
    score -= len(shared_weak) * 1.5
    
    # Spread Damage
    # Note: we can't easily check spread damage here without querying PokeAPI for every move again,
    # but we can do a simplified check for common ones if needed, or skip it.
    common_spread = {"Earthquake", "Rock Slide", "Dazzling Gleam", "Heat Wave", "Snarl", "Icy Wind", "Eruption", "Water Spout", "Make It Rain", "Hyper Voice", "Muddy Water", "Expand Force"}
    if any(m in common_spread for m in p1_moves) or any(m in common_spread for m in p2_moves):
        score += 1

    if score >= 4:
        return 'S'
    elif score >= 2:
        return 'A'
    elif score >= 0:
        return 'B'
    else:
        return 'C'

def evaluate_all_leads(team_data):
    n = len(team_data)
    matrix = [['-' for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                matrix[i][j] = calculate_lead_synergy(team_data[i], team_data[j])
    return matrix

def build_leads_matrix_html(team_data, leads_matrix):
    n = len(team_data)
    
    html = "<div style='display: flex; gap: 40px; align-items: flex-start; margin-top: 20px;'>"
    
    # Matrix table
    html += "<table style='border-collapse: collapse; text-align: center; font-size: 1.2em; font-weight: bold; background-color: rgba(255,255,255,0.02);'>"
    
    # Header row
    html += "<tr><td style='border: none;'></td>"
    for j in range(n):
        html += f"<td style='padding: 5px; border: none;'><img src='{team_data[j].get('Sprite', '')}' width='60' title='{team_data[j].get('Pokémon', '')}'></td>"
    html += "</tr>"
    
    # Rows
    for i in range(n):
        html += "<tr>"
        html += f"<td style='padding: 5px; border: none;'><img src='{team_data[i].get('Sprite', '')}' width='60' title='{team_data[i].get('Pokémon', '')}'></td>"
        for j in range(n):
            if j >= i:
                # Upper triangular and diagonal - grayed out
                html += "<td style='background-color: #8c8c8c; border: 1px solid rgba(0,0,0,0.1); width: 60px; height: 60px;'></td>"
            else:
                # Lower triangular - actual scores
                grade = leads_matrix[i][j]
                color = "inherit"
                if grade == 'S': color = "#e6e6e6"
                elif grade == 'A': color = "#e6e6e6"
                elif grade == 'B': color = "#e6e6e6"
                elif grade == 'C': color = "#e6e6e6"
                # Actually wait, the user's image shows the letters in black text on white background, 
                # but we're in dark mode. Let's make the letters white/gray.
                # Actually I'll color code the letters slightly to be cool or stick to the exact image?
                # The image just has them in black text on white cells. I'll use standard text color.
                
                html += f"<td style='padding: 10px; border: 1px solid rgba(255,255,255,0.1); width: 60px; height: 60px; color: {color}; background-color: rgba(255,255,255,0.05);'>{grade}</td>"
        html += "</tr>"
    
    html += "</table>"
    
    # Legend
    html += '''
    <div style='display: flex; flex-direction: column; justify-content: center; gap: 15px; font-size: 1.1em; padding-top: 50px;'>
        <div style='border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 5px;'><span style='font-weight: bold; margin-right: 15px;'>S</span> Strong and consistent</div>
        <div style='border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 5px;'><span style='font-weight: bold; margin-right: 15px;'>A</span> Strong and somewhat consistent</div>
        <div style='border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 5px;'><span style='font-weight: bold; margin-right: 15px;'>B</span> Weak or not very consistent</div>
        <div style='border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 5px;'><span style='font-weight: bold; margin-right: 15px;'>C</span> Niche or not usable</div>
    </div>
    '''
    html += "</div>"
    return html
