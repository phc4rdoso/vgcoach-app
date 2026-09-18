from src.pokeapi import get_move_damage_class, get_move_type


ROLE_DESCRIPTIONS = {
    "Physical Threat": "High physical attack stat relative to the meta, using physical moves.",
    "Special Threat": "High special attack stat relative to the meta, using special moves.",
    "Mixed Attacker": "Utilizes both physical and special moves with capable offenses.",
    "Fast Attacker": "High speed stat relative to the meta, allowing it to move before most opponents.",
    "Slow Attacker (TR)": "Low speed stat combined with high offense, making it a threat under Trick Room.",
    "Setup Sweeper": "Uses moves like Swords Dance or Nasty Plot to boost its stats before attacking.",
    "Choice Attacker": "Holds a Choice item (Band, Specs, Scarf) for an immediate raw stat boost.",
    "Priority User": "Has access to priority moves (like Extreme Speed, Sucker Punch) to strike first.",
    "Weather Abuser": "Abilities like Swift Swim or Chlorophyll that double speed in weather.",
    "Physical Wall": "High physical defense and HP to soak physical hits.",
    "Special Wall": "High special defense and HP to soak special hits.",
    "Mixed Wall": "High overall bulk across HP, Defense, and Special Defense.",
    "Pivot": "Uses U-turn, Volt Switch, or Parting Shot to reposition safely.",
    "Bulky Offense": "Solid bulk combined with strong attacks to take a hit and hit back hard.",
    "Stall": "Incredibly high defenses, utilizing residual damage or recovery to outlast the opponent.",
    "Speed Control": "Uses moves like Tailwind or Icy Wind to manipulate turn order.",
    "Trick Room Setter": "Has access to Trick Room to invert the turn order.",
    "Redirection": "Uses Follow Me or Rage Powder to draw incoming attacks.",
    "Weather/Terrain Setter": "Automatically sets weather/terrain upon entering or uses weather moves.",
    "Status Applicator": "Uses Spore, Will-O-Wisp, Thunder Wave, or similar to inflict status ailments.",
    "Damage Mitigation": "Uses abilities like Intimidate or moves like Reflect/Snarl to reduce incoming damage.",
    "Damage Enhancer": "Uses Helping Hand or Fake Tears to boost ally damage output.",
    "Disruption": "Prevents the opponent's strategy using Fake Out, Taunt, or Encore."
}

def determine_roles(pokemon_data, meta_avg_stats):
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
    if hp >= meta_avg_stats["HP"] * 1.05 and def_stat >= meta_avg_stats["Def"] * 1.05 and spd < meta_avg_stats["SpD"]:
        roles["Defensive"].append("Physical Wall")
    elif hp >= meta_avg_stats["HP"] * 1.05 and spd >= meta_avg_stats["SpD"] * 1.05 and def_stat < meta_avg_stats["Def"]:
        roles["Defensive"].append("Special Wall")
    elif hp >= meta_avg_stats["HP"] * 0.9 and def_stat >= meta_avg_stats["Def"] * 0.9 and spd >= meta_avg_stats["SpD"] * 0.9:
        roles["Defensive"].append("Mixed Wall")
        
    pivot_moves = {"U-turn", "Volt Switch", "Parting Shot", "Flip Turn"}
    if any(m in pivot_moves for m in moves):
        roles["Defensive"].append("Pivot")
        
    if hp >= meta_avg_stats["HP"] * 0.85 and (def_stat >= meta_avg_stats["Def"] * 0.85 or spd >= meta_avg_stats["SpD"] * 0.85) and max(atk, spa) >= max(meta_avg_stats["Atk"], meta_avg_stats["SpA"]) * 1.05 and spe <= meta_avg_stats["Spe"] * 0.95:
        roles["Defensive"].append("Bulky Offense")
        
    stall_moves = {"Sand Tomb", "Ruination", "Yawn", "Toxic", "Recover", "Roost", "Synthesis", "Protect"}
    if hp >= meta_avg_stats["HP"] * 0.95 and def_stat >= meta_avg_stats["Def"] * 0.95 and spd >= meta_avg_stats["SpD"] * 0.95 and sum(1 for m in moves if m in stall_moves) >= 2:
        roles["Defensive"].append("Stall")
        
    # OFFENSIVE ROLES
    support_count = len(roles["Support"])
    
    if atk >= meta_avg_stats["Atk"] * 1.05 and len(phys_moves) >= 2 and support_count <= 2:
        roles["Offensive"].append("Physical Threat")
    if spa >= meta_avg_stats["SpA"] * 1.05 and len(spec_moves) >= 2 and support_count <= 2:
        roles["Offensive"].append("Special Threat")
    if len(phys_moves) >= 1 and len(spec_moves) >= 1 and (atk >= meta_avg_stats["Atk"] * 0.9 and spa >= meta_avg_stats["SpA"] * 0.9) and support_count <= 2:
        roles["Offensive"].append("Mixed Attacker")
        
    if spe >= meta_avg_stats["Spe"] * 1.05 and max(atk, spa) >= max(meta_avg_stats["Atk"], meta_avg_stats["SpA"]):
        roles["Offensive"].append("Fast Attacker")
    elif spe <= meta_avg_stats["Spe"] * 0.65 and max(atk, spa) >= max(meta_avg_stats["Atk"], meta_avg_stats["SpA"]) * 1.05:
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
