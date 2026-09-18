import textwrap
import streamlit as st
from src.parser import parse_showdown_paste
import json
import pandas as pd
import altair as alt
from src.pokeapi import get_pokemon_data, calculate_stat, get_nature_multiplier, get_move_type, is_spread_damage
from src.leads import evaluate_all_leads, build_leads_matrix_html
from src.synergy import calculate_defensive_synergy, calculate_offensive_synergy, ALL_TYPES
from src.archetypes import determine_archetypes
from src.regulations import get_all_regulation_names, get_regulation
from src.meta import analyze_meta_threats, TYPE_COLORS, fetch_top_meta_pokemon
import io
import re

TYPE_IDS = {
    "Normal": 1, "Fighting": 2, "Flying": 3, "Poison": 4, "Ground": 5, "Rock": 6,
    "Bug": 7, "Ghost": 8, "Steel": 9, "Fire": 10, "Water": 11, "Grass": 12,
    "Electric": 13, "Psychic": 14, "Ice": 15, "Dragon": 16, "Dark": 17, "Fairy": 18
}

st.set_page_config(page_title="VGCoach Teambuilder", page_icon="🎮", layout="wide")

st.markdown('''
    <style>
        .block-container, [data-testid="stAppViewBlockContainer"] {
            max-width: 1400px;
            margin: 0 auto;
        }
    </style>
''', unsafe_allow_html=True)


st.title("🛡️ VGCoach - Teambuilding Assistant")
st.markdown("Paste your Pokemon Showdown team below to analyze it for the current VGC Regulation.")

tab_main, tab_faq = st.tabs(["Teambuilder & Analysis", "FAQ"])

with tab_main:
    st.sidebar.title("Configuration")
    reg_names = get_all_regulation_names()
    selected_reg_name = st.sidebar.selectbox("Select Current Regulation", reg_names, index=0)
    current_regulation = get_regulation(selected_reg_name)
    
    _, fallback_warn = fetch_top_meta_pokemon(current_regulation.name)
    if fallback_warn:
        st.warning(f"⚠️ **Notice:** {fallback_warn}")
    st.info(f"**Current Meta - {current_regulation.name}:** {current_regulation.description}")
    st.sidebar.subheader("Input Team")
    paste_input = st.sidebar.text_area("Showdown Paste or Pokepaste URL", height=250, placeholder="https://pokepast.es/...\n\nOR\n\nIncineroar @ Sitrus Berry\nAbility: Intimidate\nLevel: 50\n...")

    if st.sidebar.button("Analyze Team"):


    
        if paste_input:
            input_text = paste_input.strip()
            
            if input_text.startswith("http://") or input_text.startswith("https://"):
                with st.spinner("Fetching team from URL..."):
                    import requests
                    from bs4 import BeautifulSoup
                    
                    try:
                        url = input_text.split()[0]
                        # 1. Try pokepast.es native JSON
                        if "pokepast.es" in url:
                            json_url = url.rstrip("/") + "/json"
                            res = requests.get(json_url, timeout=5)
                            if res.status_code == 200 and "paste" in res.json():
                                input_text = res.json()["paste"]
                        
                        # 2. Fallback to HTML scraping
                        if input_text == paste_input.strip():
                            res = requests.get(url, timeout=5)
                            soup = BeautifulSoup(res.text, "html.parser")
                            articles = soup.find_all("article")
                            if articles:
                                input_text = "\n\n".join([a.get_text() for a in articles])
                            else:
                                pres = soup.find_all("pre")
                                if pres:
                                    input_text = "\n\n".join([p.get_text() for p in pres])
                                    

                    except Exception as e:
                        st.error(f"Failed to fetch team from URL. Error: {e}")
                        input_text = ""
                        
            if input_text and input_text != paste_input.strip() and input_text != url:
                st.session_state['team'] = parse_showdown_paste(input_text)
            elif input_text and not (input_text.startswith("http://") or input_text.startswith("https://")):
                st.session_state['team'] = parse_showdown_paste(input_text)
            else:
                st.warning("Could not extract a valid team from the provided link.")
        else:
            st.warning("Please enter a valid Showdown paste.")
    if 'team' in st.session_state:
        team = st.session_state['team']
    
        stats_data = []
        synergy_data_def = {t: [] for t in ALL_TYPES}
        synergy_data_off = {t: [] for t in ALL_TYPES}
        pokemon_names = []
        all_moves_in_team = set()
    
        for p in team.pokemons:
            api_data = get_pokemon_data(p.species)
            base_stats = api_data["stats"]
            p_types = api_data["types"]
            sprite_url = api_data.get("sprite", "")
        
            pokemon_names.append(p.species)
            for m in p.moves:
                all_moves_in_team.add(m)
        
            # Defensive Synergy
            defensive_mults = calculate_defensive_synergy(p_types)
            for t, mult in defensive_mults.items():
                synergy_data_def[t].append(mult)
            
            # Offensive Synergy
            move_types = [t for m in p.moves if (t := get_move_type(m)) is not None]
            offensive_mults = calculate_offensive_synergy(move_types)
            for t, mult in offensive_mults.items():
                synergy_data_off[t].append(mult)
        
            actual_stats = {}
            for stat in ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]:
                is_hp = (stat == "HP")
                base = base_stats.get(stat, 100)
                ev = p.evs.get(stat, 0)
                iv = p.ivs.get(stat, 31)
                nature_mult = get_nature_multiplier(p.nature, stat)
                actual_stats[stat] = calculate_stat(base, ev, iv, p.level, is_hp, nature_mult)
            
            stats_data.append({
                "Pokemon": p.species,
                "Sprite": sprite_url,
                "Speed": actual_stats["Spe"],
                "HP": actual_stats["HP"],
                "Atk": actual_stats["Atk"],
                "Def": actual_stats["Def"],
                "SpA": actual_stats["SpA"],
                "SpD": actual_stats["SpD"],
                "Types": p_types,
                "EVs": p.evs,
                "Item": p.item or "No Item",
                "Ability": p.ability or "Unknown",
                "Nature": p.nature,
                "Tera": p.tera_type or "Unknown",
                "Moves": p.moves
            })
        
        # 1. Pokemon Cards Display
        st.subheader("Team Details")
        card_cols = st.columns(3)
        for idx, pd_data in enumerate(stats_data):
            ev_strs = []
            for stat_name in ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]:
                if pd_data["EVs"].get(stat_name, 0) > 0:
                    ev_strs.append(f"{pd_data['EVs'][stat_name]} {stat_name}")
            ev_string = " / ".join(ev_strs) if ev_strs else "0 EVs"
        
            move_divs = []
            for m in pd_data["Moves"]:
                m_type = get_move_type(m) or "normal"
                bg_color = TYPE_COLORS.get(m_type.lower(), "#888888") + "B3"  # Add 70% opacity via hex alpha
                move_divs.append(f"<div style='background: {bg_color}; border: 1px solid rgba(0,0,0,0.2); padding: 4px 8px; border-radius: 4px; text-align: center; color: white; text-shadow: 1px 1px 2px rgba(0,0,0,0.8); font-weight: bold;'>{m}</div>")
            moves_html = "".join(move_divs)
        
            tera_html = f"<div><b>Tera Type:</b> {pd_data['Tera']}</div>" if "terastal" in current_regulation.mechanics else ""
        
            types_images = "".join([f"<img src='https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/types/generation-ix/scarlet-violet/{TYPE_IDS.get(t.capitalize(), 1)}.png' width='70' />" for t in pd_data["Types"]])
            types_html = f"<div style='display: flex; flex-direction: column; gap: 4px;'>{types_images}</div>"
        
            if pd_data['Item'] and str(pd_data['Item']).strip():
                clean_item = str(pd_data['Item']).lower().replace(" ", "-").replace("'", "")
                item_img = f"<img src='https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/{clean_item}.png' width='45' style='vertical-align: middle; margin: -10px 2px -10px -12px;'/>"
                item_html = f"<div style='font-size: 0.85em; opacity: 0.8; display: flex; align-items: center;'>{item_img} @ {pd_data['Item']}</div>"
            else:
                item_html = ""
        
            card_html = f"""
            <div style="background-color: rgba(128, 128, 128, 0.1); border: 1px solid rgba(128,128,128,0.3); border-radius: 12px; padding: 16px; margin-bottom: 16px;">
                <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid rgba(128,128,128,0.2); padding-bottom: 12px; margin-bottom: 12px;">
                    <div style="display: flex; align-items: center;">
                        <img src="{pd_data['Sprite']}" width="70" style="margin-right: 12px; filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.2));"/>
                        <div>
                            <h3 style="margin: 0; font-size: 1.1em;">{pd_data['Pokemon']}</h3>
                            {item_html}
                        </div>
                    </div>
                    {types_html}
                </div>
                <div style="font-size: 0.85em; line-height: 1.6; margin-bottom: 12px;">
                    <div><b>Ability:</b> {pd_data['Ability']}</div>
                    {tera_html}
                    <div><b>Nature:</b> {pd_data['Nature']}</div>
                    <div style="color: #4da6ff; font-weight: 500;"><b>EVs:</b> {ev_string}</div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.8em;">
                    {moves_html}
                </div>
            </div>
            """
        
            # Remove empty lines to prevent markdown parser from breaking out of HTML mode
            card_html = "\n".join([line for line in card_html.split("\n") if line.strip() != ""])
        
            with card_cols[idx % 3]:
                st.markdown(f"<div>{card_html}</div>", unsafe_allow_html=True)

        # 2. Checklist & Composition Warnings
        st.subheader("Composition Checks")
    
        # Balance Check
        from src.pokeapi import get_move_damage_class
        physical_count = 0
        special_count = 0
        for d in stats_data:
            phys_moves = sum(1 for m in d["Moves"] if get_move_damage_class(m) == 'physical')
            spec_moves = sum(1 for m in d["Moves"] if get_move_damage_class(m) == 'special')
            if phys_moves > spec_moves:
                physical_count += 1
            elif spec_moves > phys_moves:
                special_count += 1
            elif phys_moves > 0 and spec_moves > 0 and phys_moves == spec_moves:
                if d['Atk'] > d['SpA']:
                    physical_count += 1
                elif d['SpA'] > d['Atk']:
                    special_count += 1
    
        if physical_count >= 4 and special_count <= 1:
            st.warning(f"⚠️ **Unbalanced Offense:** Skewed towards Physical ({physical_count} Phys vs {special_count} Spec).")
        elif special_count >= 4 and physical_count <= 1:
            st.warning(f"⚠️ **Unbalanced Offense:** Skewed towards Special ({special_count} Spec vs {physical_count} Phys).")
        else:
            st.success(f"✅ **Balanced Offense:** ({physical_count} Phys vs {special_count} Spec).")

        # Feature Checks
        speed_control = {"Tailwind", "Icy Wind", "Trick Room", "Electroweb", "Thunder Wave"}
        damage_reduction_moves = {"Reflect", "Light Screen", "Aurora Veil", "Snarl", "Parting Shot", "Will-O-Wisp", "Charm", "Eerie Impulse"}
        damage_reduction_abilities = {"Intimidate", "Friend Guard", "Vessel of Ruin", "Tablets of Ruin", "Fluffy", "Fur Coat", "Ice Scales"}
        setup_moves = {"Swords Dance", "Nasty Plot", "Dragon Dance", "Calm Mind", "Bulk Up", "Iron Defense"}
    
        has_speed_control = any(m in speed_control for m in all_moves_in_team)
    
        has_dmg_reduction = (
            any(m in damage_reduction_moves for m in all_moves_in_team) or 
            any(getattr(p, 'ability', '') in damage_reduction_abilities for p in team.pokemons)
        )
        has_setup = any(m in setup_moves for m in all_moves_in_team)
        has_spread_damage = any(bool(is_spread_damage(m)) for m in all_moves_in_team)
        has_fake_out = "Fake Out" in all_moves_in_team
    
        weather_setters = {"Drizzle", "Drought", "Snow Warning", "Sand Stream", "Desolate Land", "Primordial Sea", "Delta Stream", "Orichalcum Pulse"}
        weather_moves = {"Rain Dance", "Sunny Day", "Snowscape", "Hail", "Sandstorm"}
        has_weather = any(getattr(p, 'ability', '') in weather_setters for p in team.pokemons) or any(m in weather_moves for m in all_moves_in_team)
    
        terrain_setters = {"Electric Surge", "Grassy Surge", "Psychic Surge", "Misty Surge", "Hadron Engine"}
        terrain_moves = {"Electric Terrain", "Grassy Terrain", "Psychic Terrain", "Misty Terrain"}
        has_terrain = any(getattr(p, 'ability', '') in terrain_setters for p in team.pokemons) or any(m in terrain_moves for m in all_moves_in_team)
    
        checks_cols = st.columns(7)
        with checks_cols[0]: st.markdown(f"{'✅' if has_speed_control else '❌'} **Speed Control**")
        with checks_cols[1]: st.markdown(f"{'✅' if has_dmg_reduction else '❌'} **Damage Reduction**")
        with checks_cols[2]: st.markdown(f"{'✅' if has_setup else '❌'} **Setup**")
        with checks_cols[3]: st.markdown(f"{'✅' if has_spread_damage else '❌'} **Spread Damage**")
        with checks_cols[4]: st.markdown(f"{'✅' if has_fake_out else '❌'} **Fake Out**")
        with checks_cols[5]: st.markdown(f"{'✅' if has_weather else '❌'} **Weather**")
        with checks_cols[6]: st.markdown(f"{'✅' if has_terrain else '❌'} **Terrain**")
        st.divider()

        # Archetypes & Stats Check
        arch_col, radar_col = st.columns([1, 1.2])
    
        with arch_col:
            st.subheader("Team Archetypes")
            archetypes_found = determine_archetypes(stats_data, all_moves_in_team, selected_reg_name)
            if archetypes_found:
                for icon, name, desc in archetypes_found:
                    st.markdown(f"### {icon} **{name}**")
                    st.caption(desc)
            else:
                st.write("No specific archetypes identified.")
            
        with radar_col:
            st.subheader("Team Average Stats vs. Top Meta Average Stats")
            st.caption("Atk and SpA averages only include Pokemon with physical or special moves. A ⚠️ appears if your team's stat is 10% lower than the top meta average stats.")
            if stats_data:
                from src.pokeapi import get_move_damage_class
            
                atk_pokemons = []
                spa_pokemons = []
            
                for d in stats_data:
                    # Check if pokemon has at least one physical or special move
                    has_phys = any(get_move_damage_class(m) == 'physical' for m in d["Moves"])
                    has_spec = any(get_move_damage_class(m) == 'special' for m in d["Moves"])
                
                    if has_phys:
                        atk_pokemons.append(d["Atk"])
                    if has_spec:
                        spa_pokemons.append(d["SpA"])
                    
                avg_atk = int(sum(atk_pokemons) / len(atk_pokemons)) if atk_pokemons else 0
                avg_spa = int(sum(spa_pokemons) / len(spa_pokemons)) if spa_pokemons else 0

                avg_stats = {
                    "HP": int(sum(d["HP"] for d in stats_data) / len(stats_data)),
                    "Atk": avg_atk,
                    "Def": int(sum(d["Def"] for d in stats_data) / len(stats_data)),
                    "Spe": int(sum(d["Speed"] for d in stats_data) / len(stats_data)),
                    "SpD": int(sum(d["SpD"] for d in stats_data) / len(stats_data)),
                    "SpA": avg_spa,
                }

                meta_list, _ = fetch_top_meta_pokemon(current_regulation.name)
                m_hps, m_atks, m_defs, m_spas, m_spds, m_spes = [], [], [], [], [], []
            
                for m in meta_list:
                    m_data = get_pokemon_data(m["species"])
                    m_base = m_data["stats"]
                    m_spread = m.get("spread")
                    if not m_spread:
                        m_spread = {"nature": "Serious", "evs": {"HP":0, "Atk":0, "Def":0, "SpA":0, "SpD":0, "Spe":0}}
                    
                    m_actual = {}
                    for stat_name in ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]:
                        is_hp = (stat_name == "HP")
                        b = m_base.get(stat_name, 100)
                        ev = m_spread["evs"].get(stat_name, 0)
                        nature_mult = get_nature_multiplier(m_spread["nature"], stat_name)
                        m_actual[stat_name] = calculate_stat(b, ev, 31, 50, is_hp, nature_mult)
                    
                    m_hps.append(m_actual["HP"])
                    m_defs.append(m_actual["Def"])
                    m_spds.append(m_actual["SpD"])
                    m_spes.append(m_actual["Spe"])
                
                    phys_moves = sum(1 for move in m.get("moves", []) if get_move_damage_class(move) == "physical")
                    spec_moves = sum(1 for move in m.get("moves", []) if get_move_damage_class(move) == "special")
                    if phys_moves == 0 and spec_moves == 0:
                        if m_base.get("Atk", 0) > m_base.get("SpA", 0):
                            phys_moves = 1
                        else:
                            spec_moves = 1
                        
                    if phys_moves > 0:
                        m_atks.append(m_actual["Atk"])
                    if spec_moves > 0:
                        m_spas.append(m_actual["SpA"])

                meta_avg_stats = {
                    "HP": int(sum(m_hps)/len(m_hps)) if m_hps else 100,
                    "Atk": int(sum(m_atks)/len(m_atks)) if m_atks else 100,
                    "Def": int(sum(m_defs)/len(m_defs)) if m_defs else 100,
                    "Spe": int(sum(m_spes)/len(m_spes)) if m_spes else 100,
                    "SpD": int(sum(m_spds)/len(m_spds)) if m_spds else 100,
                    "SpA": int(sum(m_spas)/len(m_spas)) if m_spas else 100,
                }
            
                import math
            
                # SVG Dimensions
                width = 380
                height = 380
                cx = width / 2
                cy = 175
                max_radius = 120
            
                # Requested sort order: HP top, Atk top-right, Def bottom-right, Spe bottom, SpD bottom-left, SpA top-left
                sort_order = ["HP", "Atk", "Def", "Spe", "SpD", "SpA"]
                max_val = max(150, max(list(avg_stats.values()) + list(meta_avg_stats.values())) + 20)
            
                # Angles (-pi/2 is Top in SVG)
                angles = [-math.pi/2 + i * (2 * math.pi / 6) for i in range(6)]
            
                def get_xy(val, angle):
                    r = (val / max_val) * max_radius
                    return cx + r * math.cos(angle), cy + r * math.sin(angle)
            
                svg = f'<div style="display: flex; justify-content: center;"><svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
            
                # Background Grid
                for r_pct in [0.333, 0.666, 1.0]:
                    points = []
                    for a in angles:
                        x = cx + (max_radius * r_pct) * math.cos(a)
                        y = cy + (max_radius * r_pct) * math.sin(a)
                        points.append(f"{x},{y}")
                    svg += f'<polygon points="{" ".join(points)}" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>'
                
                # Axes
                for a in angles:
                    x = cx + max_radius * math.cos(a)
                    y = cy + max_radius * math.sin(a)
                    svg += f'<line x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>'
                
                # Stats Polygon (Filled)
                stat_points = []
                for i, stat in enumerate(sort_order):
                    x, y = get_xy(avg_stats[stat], angles[i])
                    stat_points.append(f"{x},{y}")
                
                # Meta Stats Polygon (Red)
                meta_points = []
                for i, stat in enumerate(sort_order):
                    x, y = get_xy(meta_avg_stats[stat], angles[i])
                    meta_points.append(f"{x},{y}")
                
                svg += f'<polygon points="{" ".join(meta_points)}" fill="rgba(255, 77, 77, 0.4)" stroke="#ff4d4d" stroke-width="3"/>'
            
                svg += f'<polygon points="{" ".join(stat_points)}" fill="rgba(77, 166, 255, 0.4)" stroke="#4da6ff" stroke-width="3"/>'
            
                # Points and Labels
                for i, stat in enumerate(sort_order):
                    # Meta point
                    mx, my = get_xy(meta_avg_stats[stat], angles[i])
                    svg += f'<circle cx="{mx}" cy="{my}" r="4.5" fill="#ff4d4d"/>'
                
                    # Team point
                    val = avg_stats[stat]
                    x, y = get_xy(val, angles[i])
                    svg += f'<circle cx="{x}" cy="{y}" r="4.5" fill="#4da6ff"/>'
                
                    lx = cx + (max_radius + 28) * math.cos(angles[i])
                    ly = cy + (max_radius + 28) * math.sin(angles[i])
                
                    anchor = "middle"
                    if math.cos(angles[i]) > 0.1:
                        anchor = "start"
                    elif math.cos(angles[i]) < -0.1:
                        anchor = "end"
                    
                    meta_val = meta_avg_stats[stat]
                
                    # If team's average is 10% or more below the meta's average, display a warning
                    stat_display = stat
                    if val < meta_val * 0.90:
                        stat_display = f"⚠️ {stat}"
                    
                    svg += f'<text x="{lx}" y="{ly - 4}" fill="#e0e0e0" font-size="13" font-weight="bold" font-family="sans-serif" text-anchor="{anchor}">{stat_display}</text>'
                
                    svg += f'<text x="{lx}" y="{ly + 14}" font-size="12" font-family="sans-serif" text-anchor="{anchor}">'
                    svg += f'<tspan fill="#4da6ff">{val}</tspan>'
                    svg += f'<tspan fill="#e0e0e0"> / </tspan>'
                    svg += f'<tspan fill="#ff4d4d">{meta_val}</tspan>'
                    svg += '</text>'
                
            
            
                # Add legend
                svg += f'''
                    <g transform="translate({cx - 120}, {height - 15})">
                        <rect x="0" y="0" width="12" height="12" fill="rgba(77, 166, 255, 0.4)" stroke="#4da6ff"/>
                        <text x="20" y="10" fill="white" font-size="12" font-family="sans-serif">Team Stats</text>
                        <rect x="130" y="0" width="12" height="12" fill="rgba(255, 77, 77, 0.4)" stroke="#ff4d4d"/>
                        <text x="150" y="10" fill="white" font-size="12" font-family="sans-serif">Top Meta Stats</text>
                    </g>
                </svg></div>
                '''
                st.markdown(f"<div>{svg}</div>", unsafe_allow_html=True)

        st.divider()
        # Type Triangles Check
        TYPE_TRIANGLES = [
            ("Fire", "Grass", "Water"),
            ("Fire", "Steel", "Rock"),
            ("Grass", "Ground", "Poison"),
            ("Fighting", "Rock", "Flying"),
            ("Dragon", "Fairy", "Steel"),
            ("Dark", "Psychic", "Fighting")
        ]
    
        team_types = set()
        for p in team.pokemons:
            for t in get_pokemon_data(p.species)["types"]:
                team_types.add(t)
            
        triangles_found = [tri for tri in TYPE_TRIANGLES if all(t in team_types for t in tri)]
    
        st.subheader("Perfect Type Triangles Detected")
        st.caption("*A perfect type triangle is a core where each type hits the next super-effectively and resists it in return.*")
    
        if triangles_found:
            badges_html = ""
            for tri in triangles_found:
                badges_html += f"<div style='display: inline-flex; align-items: center; background-color: rgba(128,128,128,0.1); border-radius: 8px; padding: 10px; margin-right: 15px; margin-bottom: 15px; border: 1px solid rgba(128,128,128,0.3); gap: 10px;'>"
                badges_html += f"<img src='https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/types/generation-ix/scarlet-violet/{TYPE_IDS[tri[0]]}.png' width='75' />"
                badges_html += f"<span style='font-size: 1.2em; font-weight: bold; color: rgba(255,255,255,0.5);'>➔</span>"
                badges_html += f"<img src='https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/types/generation-ix/scarlet-violet/{TYPE_IDS[tri[1]]}.png' width='75' />"
                badges_html += f"<span style='font-size: 1.2em; font-weight: bold; color: rgba(255,255,255,0.5);'>➔</span>"
                badges_html += f"<img src='https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/types/generation-ix/scarlet-violet/{TYPE_IDS[tri[2]]}.png' width='75' />"
                badges_html += "</div>"
            st.markdown(f"<div style='display: flex; flex-wrap: wrap;'>{badges_html}</div>", unsafe_allow_html=True)
        else:
            st.warning("⚠️ **No Type Triangles Detected:** This team does not contain a complete perfect type core (e.g., Fire/Water/Grass, Fantasy, or Dark/Psychic/Fighting).")
        
        st.divider()
    
        # Top Meta Threats
        st.subheader("Top Meta Threats")
        st.caption("*Highlights top meta Pokemon that can hit multiple members of your team super-effectively while resisting your return hits.*")
    
        threats = analyze_meta_threats(team, selected_reg_name)
        if threats:
            threats_html = """<style>
.threat-tooltip-container {
    position: relative;
    cursor: help;
    display: flex; 
    flex-direction: column; 
    align-items: center; 
    border-radius: 8px; 
    padding: 10px; 
    width: 100px;
}
.threat-tooltip-container .threat-tooltip-text {
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
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    border: 1px solid rgba(255,255,255,0.1);
    font-size: 0.75rem;
    font-weight: normal;
    line-height: 1.4;
    pointer-events: none;
}
.threat-tooltip-container:hover .threat-tooltip-text {
    visibility: visible;
    opacity: 1;
    transform: translateX(-50%) translateY(-2px);
}
</style>
<div style='display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 20px;'>
"""
            for th in threats:
                score = th.get("score", 0)
                if score >= 4:
                    bg = "rgba(255, 50, 50, 0.15)"
                    border = "rgba(255, 50, 50, 0.4)"
                else:
                    bg = "rgba(255, 200, 50, 0.1)"
                    border = "rgba(255, 200, 50, 0.3)"
                
                threats_html += f"""<div class="threat-tooltip-container" style="background-color: {bg}; border: 1px solid {border};">
<img src="{th['sprite']}" width="75" />
<span style="font-size: 0.8em; font-weight: bold; text-align: center; word-wrap: break-word;">{th['species']}</span>
<div class="threat-tooltip-text"><strong>Threat Analysis:</strong><br/>{th['explanation']}</div>
</div>"""
            threats_html += "</div>"
            st.markdown(f"<div>{threats_html}</div>", unsafe_allow_html=True)
        else:
            st.success("✅ **No major meta threats detected!** Your team handles the top 30 meta Pokemon well.")
        
        st.divider()

        # Lead Combinations Matrix
        st.subheader("Lead Combinations Matrix")
        leads_matrix = evaluate_all_leads(stats_data)
        leads_html = build_leads_matrix_html(stats_data, leads_matrix)
        st.markdown(f"<div>{leads_html}</div>", unsafe_allow_html=True)
        st.caption("*Leads are evaluated based on Fake Out + Setup/Attacker synergy, Speed Control synergy, Weather/Terrain synergy, shared weaknesses, and more.*")
        st.divider()

        # 3. Defensive and Offensive Matrices
        st.subheader("Type Synergy Matrices")
    
        def format_synergy_html(val):
            if val == 2.0: return "<span style='color: #ff6666; font-weight: bold;'>2x</span>"
            if val == 4.0: return "<span style='color: #ff6666; font-weight: bold;'>4x</span>"
            if val == 0.5: return "<span style='color: #66cc66; font-weight: bold;'>1/2</span>"
            if val == 0.25: return "<span style='color: #66cc66; font-weight: bold;'>1/4</span>"
            if val == 0.0: return "<span style='color: #aaaaaa; font-weight: bold;'>immune</span>"
            return ""

        def build_synergy_html(synergy_data, is_defensive=True):
            headers = ["Type"] + [f"<img src='{d['Sprite']}' width='45' title='{d['Pokemon']}'>" for d in stats_data]
            if is_defensive:
                headers += ["Total Weak", "Total Resist"]
            else:
                headers += ["Not Very Effective", "Super Effective"]
            
            border_color = "rgba(80,80,80,0.6)"
            html = f"<div style='border-radius: 12px; overflow: hidden; border: 1px solid {border_color};'>"
            html += f"<table style='width: 100%; border-collapse: collapse; text-align: center; font-size: 0.9em; table-layout: fixed; margin: 0;'>"
            html += "<tr>"
            for idx, h in enumerate(headers):
                width_style = "width: 12%;" if idx == 0 else "" # Give type col slightly more space
                html += f"<th style='padding: 4px; border: 1px solid {border_color}; background-color: rgba(128,128,128,0.1); {width_style}'>{h}</th>"
            html += "</tr>"
        
            def bad_total_style(n):
                if n == 0: return "color: inherit;"
                if 1 <= n <= 2: return "background-color: rgba(200, 200, 50, 0.2); color: white; font-weight: bold;"
                return "background-color: rgba(200, 50, 50, 0.3); color: white; font-weight: bold;"
            
            def good_total_style(n):
                if n == 0: return "color: inherit;"
                alpha = min(0.1 + n * 0.08, 0.4)
                return f"background-color: rgba(50, 200, 50, {alpha}); color: white; font-weight: bold;"

            for t in ALL_TYPES:
                html += "<tr>"
                html += f"<td style='padding: 4px; border: 1px solid {border_color}; font-weight: bold; text-align: center;'><img src='https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/types/generation-ix/scarlet-violet/{TYPE_IDS[t]}.png' width='75' title='{t}'></td>"
                row_vals = synergy_data[t]
                for val in row_vals:
                    html += f"<td style='padding: 4px; border: 1px solid {border_color};'>{format_synergy_html(val)}</td>"
            
                # Totals
                if is_defensive:
                    total_resist = sum(1 for v in row_vals if v < 1.0)
                    total_weak = sum(1 for v in row_vals if v > 1.0)
                    html += f"<td style='padding: 4px; border: 1px solid {border_color}; {bad_total_style(total_weak)}'>{total_weak}</td>"
                    html += f"<td style='padding: 4px; border: 1px solid {border_color}; {good_total_style(total_resist)}'>{total_resist}</td>"
                else:
                    total_nve = sum(1 for v in row_vals if v < 1.0)
                    total_se = sum(1 for v in row_vals if v > 1.0)
                    html += f"<td style='padding: 4px; border: 1px solid {border_color}; {bad_total_style(total_nve)}'>{total_nve}</td>"
                    html += f"<td style='padding: 4px; border: 1px solid {border_color}; {good_total_style(total_se)}'>{total_se}</td>"
                html += "</tr>"
            
            html += "</table></div>"
            return html

        st.write("**Defensive Coverage**")
        st.markdown(f"<div>{build_synergy_html(synergy_data_def, is_defensive=True)}</div>", unsafe_allow_html=True)
        st.markdown("<br><strong>Offensive Coverage</strong>", unsafe_allow_html=True)
        st.markdown(f"<div>{build_synergy_html(synergy_data_off, is_defensive=False)}</div>", unsafe_allow_html=True)


    else:
        st.info("Paste your team in the sidebar to see the breakdown.")

with tab_faq:
    st.header("Frequently Asked Questions (FAQ)")

    with st.expander("How are team archetypes considered?"):
        st.markdown("""
        The app analyzes the total sum of mechanics across your 6 Pokémon to guess the archetype:
    - **Tailwind / Hyper Offense:** Requires multiple speed control moves (like Tailwind or Icy Wind) and high spread damage.
    - **Trick Room:** Triggered if your team contains multiple Trick Room setters and abusers (slow Pokémon with high attacking stats).
    - **Weather (Rain/Sun/Snow/Sand):** Triggered if you have a weather-setting ability (e.g., Drizzle, Drought) combined with abusers (e.g., Swift Swim, Chlorophyll) and weather-synergistic moves.
    - **Setup / Bulky Offense:** Triggered by multiple setup moves (Swords Dance, Calm Mind) combined with damage reduction (Intimidate, screens, Snarl).
        """)

    with st.expander("How are the Team Average Stats and Top Meta Stats calculated?"):
        st.markdown("""
        - **Team Average:** We extract the EVs and Natures from your paste and run them through the level 50 Pokémon stat formula (`((2 * Base + IV + EV/4) * 50 / 100 + 5) * Nature`). The chart averages these true stats across your team. For Attack and Special Attack, it only averages Pokémon that actually use physical or special moves.
    - **Top Meta:** We download the most recent Smogon VGC `.txt.gz` usage stats for the current regulation. We take the top 30 most used Pokémon, parse their most popular EV spread and Nature, calculate their level 50 stats, and average them. If your team's stat is more than 10% lower than the meta average, a ⚠️ warning appears.
        """)

    with st.expander("Which Perfect Type Triangles are considered valid?"):
        st.markdown("""
        The app checks for six major perfect type triangles where each type both hits the next super-effectively and resists it in return:
    - **Fire / Water / Grass** (The classic FWG core)
    - **Fairy / Dragon / Steel** (The Fantasy FDS core)
    - **Dark / Psychic / Fighting** (The classic DPF core)
    - **Fire / Steel / Rock**
    - **Grass / Ground / Poison**
    - **Fighting / Rock / Flying**

    A triangle is complete if your team possesses at least one Pokemon with each of the three types in a core. This guarantees strong defensive pivoting and offensive coverage.
        """)

    with st.expander('How are "Meta Threats" decided?'):
        st.markdown("""
        We analyze the top 30 most used Pokémon in the selected regulation (from Smogon data). A Pokémon is considered a threat based on a scoring system:
    - **Offensive Threat:** It has a highly-used STAB or coverage move that hits multiple members of your team for Super Effective (2x or 4x) damage.
    - **Defensive Gap:** No Pokémon on your team has a move that hits it for Super Effective damage.
    - **Ability Punishments:** It possesses an ability that counters your team (e.g., it has Defiant/Competitive and you rely on Intimidate, or it has Swift Swim and you set Rain).
        """)

    with st.expander("How is the Lead Combination Tier calculated?"):
        st.markdown("""
        The Lead Matrix evaluates all 15 possible 2-Pokémon lead combinations on your team using a points-based system:
    - **Synergy (+):** Points are awarded for complementary pairs, such as Fake Out + Setup (e.g., Swords Dance), Speed Control (Tailwind) + Spread Damage (e.g., Earthquake, Dazzling Gleam), or Weather Setter + Weather Abuser.
    - **Anti-Synergy (-):** Points are deducted for conflicting mechanics (e.g., Trick Room + Tailwind on the same lead, or double Intimidate risking a Defiant boost without immediate offensive pressure).
    The tier (S, A, B, C) reflects the net score of the pair.
        """)

