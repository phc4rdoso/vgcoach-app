from src.pokeapi import get_move_damage_class, get_move_type

def determine_roles(pokemon_data):
    roles = {
        "Offensive": [],
        "Defensive": [],
        "Support": []
    }
    
    moves = pokemon_data.get('Moves', [])
    ability = pokemon_data.get('Ability', '')
    item = pokemon_data.get('Item', '')
    
    # Stats
    hp = pokemon_data.get('HP', 0)
    atk = pokemon_data.get('Atk', 0)
    def_stat = pokemon_data.get('Def', 0)
    spa = pokemon_data.get('SpA', 0)
    spd = pokemon_data.get('SpD', 0)
    spe = pokemon_data.get('Speed', 0)
    
    # Move analysis
    phys_moves = [m for m in moves if get_move_damage_class(m) == 'physical']
    spec_moves = [m for m in moves if get_move_damage_class(m) == 'special']
    status_moves = [m for m in moves if get_move_damage_class(m) == 'status']
    
    # SUPPORT ROLES
    speed_control_moves = {"Tailwind", "Thunder Wave", "Icy Wind", "Electroweb"}
    if any(m in speed_control_moves for m in moves):
        roles["Support"].append("Speed Control")
        
    if "Trick Room" in moves:
        roles["Support"].append("Trick Room Setter")
        
    redirection_moves = {"Follow Me", "Rage Powder"}
    if any(m in redirection_moves for m in moves):
        roles["Support"].append("Redirection")
        
    weather_abilities = {"Drizzle", "Drought", "Sand Stream", "Snow Warning", "Orichalcum Pulse", "Hadron Engine"}
    weather_moves = {"Rain Dance", "Sunny Day", "Sandstorm", "Snowscape"}
    if ability in weather_abilities or any(m in weather_moves for m in moves):
        roles["Support"].append("Weather/Terrain Setter")
        
    status_inflict = {"Thunder Wave", "Will-O-Wisp", "Spore", "Sleep Powder", "Hypnosis", "Yawn", "Toxic"}
    if any(m in status_inflict for m in moves):
        roles["Support"].append("Status Applicator")
        
    mitigation_moves = {"Snarl", "Parting Shot", "Will-O-Wisp", "Reflect", "Light Screen", "Aurora Veil"}
    mitigation_abilities = {"Intimidate", "Friend Guard", "Vessel of Ruin", "Tablets of Ruin", "Fluffy", "Fur Coat"}
    if ability in mitigation_abilities or any(m in mitigation_moves for m in moves):
        roles["Support"].append("Damage Mitigation")
        
    enhancer_moves = {"Helping Hand", "Howl", "Coaching", "Decorate", "Fake Tears", "Screech"}
    if any(m in enhancer_moves for m in moves):
        roles["Support"].append("Damage Enhancer")
        
    disruption_moves = {"Fake Out", "Taunt", "Encore", "Imprison", "Wide Guard", "Quick Guard"}
    disruption_abilities = {"Shadow Tag"}
    if ability in disruption_abilities or any(m in disruption_moves for m in moves):
        roles["Support"].append("Disruption")
        
    # DEFENSIVE ROLES
    if hp >= 100 and def_stat >= 100 and spd < 100:
        roles["Defensive"].append("Physical Wall")
    elif hp >= 100 and spd >= 100 and def_stat < 100:
        roles["Defensive"].append("Special Wall")
    elif hp >= 90 and def_stat >= 90 and spd >= 90:
        roles["Defensive"].append("Mixed Wall")
        
    pivot_moves = {"U-turn", "Volt Switch", "Parting Shot", "Flip Turn"}
    if any(m in pivot_moves for m in moves):
        roles["Defensive"].append("Pivot")
        
    if hp >= 85 and (def_stat >= 85 or spd >= 85) and max(atk, spa) >= 110 and spe <= 90:
        roles["Defensive"].append("Bulky Offense")
        
    stall_moves = {"Sand Tomb", "Ruination", "Yawn", "Toxic", "Recover", "Roost", "Synthesis", "Protect"}
    if hp >= 95 and def_stat >= 95 and spd >= 95 and sum(1 for m in moves if m in stall_moves) >= 2:
        roles["Defensive"].append("Stall")
        
    # OFFENSIVE ROLES
    if atk >= 110 and len(phys_moves) >= 2:
        roles["Offensive"].append("Physical Threat")
    if spa >= 110 and len(spec_moves) >= 2:
        roles["Offensive"].append("Special Threat")
    if len(phys_moves) >= 1 and len(spec_moves) >= 1 and (atk >= 90 and spa >= 90):
        roles["Offensive"].append("Mixed Attacker")
        
    if spe >= 110 and max(atk, spa) >= 100:
        roles["Offensive"].append("Fast Attacker")
    elif spe <= 60 and max(atk, spa) >= 110:
        roles["Offensive"].append("Slow Attacker (TR)")
        
    weather_abusers = {"Swift Swim", "Chlorophyll", "Protosynthesis", "Sand Rush", "Slush Rush", "Solar Power", "Quark Drive"}
    if ability in weather_abusers:
        roles["Offensive"].append("Weather Abuser")
        
    setup_moves = {"Swords Dance", "Nasty Plot", "Dragon Dance", "Quiver Dance", "Calm Mind", "Bulk Up", "Iron Defense", "Coil"}
    if any(m in setup_moves for m in moves):
        roles["Offensive"].append("Setup Sweeper")
        
    priority_moves = {"Extreme Speed", "Sucker Punch", "Thunderclap", "Jet Punch", "Aqua Jet", "Bullet Punch", "Ice Shard", "Grassy Glide", "Mach Punch", "Vacuum Wave", "Fake Out"}
    # don't count Fake Out as priority sweeper
    true_priority = set(priority_moves) - {"Fake Out"}
    if any(m in true_priority for m in moves):
        roles["Offensive"].append("Priority User")
        
    if isinstance(item, str) and ("Choice" in item):
        roles["Offensive"].append("Choice Attacker")

    return roles
