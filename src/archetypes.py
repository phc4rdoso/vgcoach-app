def determine_archetypes(team_data, all_moves):
    archetypes = []
    
    # 1. Weather
    weather_abilities = {"Drizzle", "Drought", "Sand Stream", "Snow Warning", "Orichalcum Pulse", "Desolate Land", "Primordial Sea"}
    has_weather = any(p.get('Ability') in weather_abilities for p in team_data)
    if has_weather:
        archetypes.append(("🌤️", "Weather", "Relies on weather conditions to boost attacks or trigger abilities."))
        
    # 2. Trick Room
    if "Trick Room" in all_moves:
        archetypes.append(("⏳", "Trick Room", "Uses Trick Room to reverse the turn order, allowing slow Pokémon to move first."))
        
    # 3. Setup
    setup_moves = {"Swords Dance", "Nasty Plot", "Dragon Dance", "Calm Mind", "Bulk Up", "Iron Defense", "Quiver Dance", "Coil"}
    has_setup = any(m in setup_moves for m in all_moves)
    pokemon_names = [p.get('Pokémon', '') for p in team_data]
    if has_setup or ("Dondozo" in pokemon_names and "Tatsugiri" in pokemon_names):
        archetypes.append(("📈", "Setup", "Focuses on boosting stats to sweep the opposing team."))
        
    # Calculate stats for the rest
    if team_data:
        avg_speed = sum(p.get('Spe', 100) for p in team_data) / len(team_data)
        # avg_bulk is the average of (HP + Def + SpD) / 3 per Pokemon
        avg_bulk = sum((p.get('HP', 100) + p.get('Def', 100) + p.get('SpD', 100)) / 3 for p in team_data) / len(team_data)
    else:
        avg_speed = 100
        avg_bulk = 100

    # 4. Stall
    stall_moves = {"Toxic", "Toxic Spikes", "Recover", "Roost", "Slack Off", "Synthesis", "Morning Sun", "Moonlight", "Leech Seed", "Protect"}
    recovery_count = sum(1 for m in all_moves if m in stall_moves)
    if recovery_count >= 5 and avg_bulk > 93:
        archetypes.append(("🧱", "Stall", "Aims to outlast the opponent with high defenses, recovery, and passive damage."))
        
    # 5. Hyper Offense
    speed_control_moves = {"Tailwind", "Icy Wind", "Electroweb"}
    has_fast_speed_control = any(m in speed_control_moves for m in all_moves)
    if avg_speed > 95 and avg_bulk < 85:
        archetypes.append(("🚀", "Hyper Offense", "Prioritizes speed and damage to overwhelm the opponent quickly."))
        
    # 6. Bulky Offense
    elif avg_bulk > 85 and avg_speed < 90 and "Trick Room" not in all_moves:
        archetypes.append(("🛡️", "Bulky Offense", "Uses naturally bulky attackers that can take hits and hit back hard."))
        
    # 7. Balance
    elif ("Fake Out" in all_moves or "Incineroar" in pokemon_names) and avg_bulk >= 76:
        archetypes.append(("⚖️", "Balance", "A flexible composition with a mix of offense, defense, and support."))
        
    # Fallback
    if not archetypes:
         archetypes.append(("🎭", "Standard/Flex", "A balanced or unique team composition that doesn't strictly fit a single core archetype."))
         
    return archetypes
