def determine_archetypes(team_data, all_moves, regulation_name=""):
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
        avg_speed = sum(p.get('Speed', 100) for p in team_data) / len(team_data)
        # avg_bulk is the average of (HP + Def + SpD) / 3 per Pokemon
        avg_bulk = sum((p.get('HP', 100) + p.get('Def', 100) + p.get('SpD', 100)) / 3 for p in team_data) / len(team_data)
    else:
        avg_speed = 100
        avg_bulk = 100

    # Calculate dynamic meta thresholds
    meta_speed = 120.0  # Default fallback (around base 85 fully invested)
    meta_bulk = 135.0   # Default fallback (around base 85-90 slightly invested)
    
    if regulation_name:
        try:
            from src.meta import fetch_top_meta_pokemon
            from src.pokeapi import get_pokemon_data, calculate_stat, get_nature_multiplier
            meta_list, _ = fetch_top_meta_pokemon(regulation_name)
            
            if meta_list:
                speeds = []
                bulks = []
                for m in meta_list:
                    api_data = get_pokemon_data(m["species"])
                    if not api_data:
                        continue
                        
                    base_stats = api_data["stats"]
                    spread = m.get("spread") or {"nature": "Serious", "evs": {}}
                    evs = spread.get("evs", {})
                    nature = spread.get("nature", "Serious")
                    
                    # calc Speed
                    base_spe = base_stats.get("Spe", 100)
                    ev_spe = evs.get("Spe", 0)
                    nat_mult = get_nature_multiplier(nature, "Spe")
                    speeds.append(calculate_stat(base_spe, ev_spe, 31, 50, False, nat_mult))
                    
                    # calc Bulk
                    base_hp = base_stats.get("HP", 100)
                    act_hp = calculate_stat(base_hp, evs.get("HP", 0), 31, 50, True, 1.0)
                    
                    base_def = base_stats.get("Def", 100)
                    act_def = calculate_stat(base_def, evs.get("Def", 0), 31, 50, False, get_nature_multiplier(nature, "Def"))
                    
                    base_spd = base_stats.get("SpD", 100)
                    act_spd = calculate_stat(base_spd, evs.get("SpD", 0), 31, 50, False, get_nature_multiplier(nature, "SpD"))
                    
                    bulks.append((act_hp + act_def + act_spd) / 3)
                    
                if speeds and bulks:
                    meta_speed = sum(speeds) / len(speeds)
                    meta_bulk = sum(bulks) / len(bulks)
        except Exception:
            pass # Fall back to defaults if something goes wrong

    # 4. Stall
    stall_moves = {"Toxic", "Toxic Spikes", "Recover", "Roost", "Slack Off", "Synthesis", "Morning Sun", "Moonlight", "Leech Seed", "Protect", "Will-O-Wisp", "Snarl", "Parting Shot", "Spiky Shield"}
    recovery_count = sum(1 for m in all_moves if m in stall_moves)
    # VGC stall requires fewer recovery moves than singles. It's more about bulk and passive damage/drops.
    if recovery_count >= 4 and avg_bulk > (meta_bulk * 1.08):
        archetypes.append(("🧱", "Stall / Hard Control", "Aims to outlast the opponent with high defenses, recovery, and stat drops."))
        
    # 5. Hyper Offense
    if avg_speed > (meta_speed * 1.05) and avg_bulk < (meta_bulk * 0.96):
        archetypes.append(("🚀", "Hyper Offense", "Prioritizes speed and damage to overwhelm the opponent quickly."))
        
    # 6. Bulky Offense
    elif avg_bulk > (meta_bulk * 1.03) and avg_speed < (meta_speed * 0.97) and "Trick Room" not in all_moves:
        archetypes.append(("🛡️", "Bulky Offense", "Uses naturally bulky attackers that can take hits and hit back hard."))
        
    # 7. Balance
    elif ("Fake Out" in all_moves or "Incineroar" in pokemon_names or "Rillaboom" in pokemon_names) and avg_bulk >= (meta_bulk * 0.95):
        archetypes.append(("⚖️", "Balance", "A flexible composition with a mix of offense, defense, and support."))
        
    # Fallback
    if not archetypes:
         archetypes.append(("🎭", "Standard/Flex", "A balanced or unique team composition that doesn't strictly fit a single core archetype."))
         
    return archetypes
