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

st.set_page_config(page_title="VGCoach Teambuilder", page_icon="🎮", layout="wide")

st.title("🛡️ VGCoach - Teambuilding Assistant")
st.markdown("Paste your Pokémon Showdown team below to analyze it for the current VGC Regulation.")

# Regulation Selector
reg_names = get_all_regulation_names()
selected_reg_name = st.selectbox("Select Current Regulation", reg_names, index=0)
current_regulation = get_regulation(selected_reg_name)
st.info(f"**Current Meta - {current_regulation.name}:** {current_regulation.description}")

col1, col2 = st.columns([1, 2.5])

with col1:
    st.subheader("Input Team")
    paste_input = st.text_area("Showdown Paste", height=250, placeholder="Incineroar @ Sitrus Berry\nAbility: Intimidate\nLevel: 50\n...")
    
    if st.button("Analyze Team"):
        if paste_input:
            st.session_state['team'] = parse_showdown_paste(paste_input)
        else:
            st.warning("Please enter a valid Showdown paste.")

with col2:
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
                "Pokémon": p.species,
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
            moves_html = "".join([f"<div style='background: rgba(128,128,128,0.2); padding: 4px 8px; border-radius: 4px; text-align: center;'>{m}</div>" for m in pd_data["Moves"]])
            with card_cols[idx % 3]:
                st.markdown(f"""
                <div style="background-color: rgba(128, 128, 128, 0.1); border: 1px solid rgba(128,128,128,0.3); border-radius: 12px; padding: 16px; margin-bottom: 16px;">
                    <div style="display: flex; align-items: center; border-bottom: 1px solid rgba(128,128,128,0.2); padding-bottom: 12px; margin-bottom: 12px;">
                        <img src="{pd_data['Sprite']}" width="70" style="margin-right: 12px; filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.2));"/>
                        <div>
                            <h3 style="margin: 0; font-size: 1.1em;">{pd_data['Pokémon']}</h3>
                            <div style="font-size: 0.85em; opacity: 0.8;">@ {pd_data['Item']}</div>
                        </div>
                    </div>
                    <div style="font-size: 0.85em; line-height: 1.6; margin-bottom: 12px;">
                        <div><b>Ability:</b> {pd_data['Ability']}</div>
                        <div><b>Tera Type:</b> {pd_data['Tera']}</div>
                        <div><b>Nature:</b> {pd_data['Nature']}</div>
                        <div style="color: #4da6ff; font-weight: 500;"><b>EVs:</b> {ev_string}</div>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.8em;">
                        {moves_html}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # 2. Checklist & Composition Warnings
        st.subheader("Composition Checks")
        
        # Balance Check
        physical_count = sum(1 for d in stats_data if d['Atk'] > d['SpA'] + 15)
        special_count = sum(1 for d in stats_data if d['SpA'] > d['Atk'] + 15)
        
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
        has_spread_damage = any(is_spread_damage(m) for m in all_moves_in_team)
        has_fake_out = "Fake Out" in all_moves_in_team
        
        checks_cols = st.columns(5)
        with checks_cols[0]: st.markdown(f"{'✅' if has_speed_control else '❌'} **Speed Control**")
        with checks_cols[1]: st.markdown(f"{'✅' if has_dmg_reduction else '❌'} **Damage Reduc.**")
        with checks_cols[2]: st.markdown(f"{'✅' if has_setup else '❌'} **Setup**")
        with checks_cols[3]: st.markdown(f"{'✅' if has_spread_damage else '❌'} **Spread Dmg**")
        with checks_cols[4]: st.markdown(f"{'✅' if has_fake_out else '❌'} **Fake Out**")
        st.divider()

        # Archetypes & Stats Check
        arch_col, radar_col = st.columns([1, 1.2])
        
        with arch_col:
            st.subheader("Team Archetypes")
            archetypes_found = determine_archetypes(stats_data, all_moves_in_team)
            if archetypes_found:
                for icon, name, desc in archetypes_found:
                    st.markdown(f"### {icon} **{name}**")
                    st.caption(desc)
            else:
                st.write("No specific archetypes identified.")
                
        with radar_col:
            st.subheader("Team Average Stats")
            if stats_data:
                avg_stats = {
                    "HP": int(sum(d["HP"] for d in stats_data) / len(stats_data)),
                    "Atk": int(sum(d["Atk"] for d in stats_data) / len(stats_data)),
                    "Def": int(sum(d["Def"] for d in stats_data) / len(stats_data)),
                    "SpA": int(sum(d["SpA"] for d in stats_data) / len(stats_data)),
                    "SpD": int(sum(d["SpD"] for d in stats_data) / len(stats_data)),
                    "Spe": int(sum(d["Speed"] for d in stats_data) / len(stats_data)),
                }
                
                import math
                sort_order = ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]
                df_avg = pd.DataFrame([{"Stat": k, "Value": avg_stats[k]} for k in sort_order])
                
                max_val = max(150, df_avg['Value'].max() + 20)
                
                angles = [math.pi/2 - i * (2 * math.pi / 6) for i in range(6)]
                df_avg['x'] = [val * math.cos(angles[i]) for i, val in enumerate(df_avg['Value'])]
                df_avg['y'] = [val * math.sin(angles[i]) for i, val in enumerate(df_avg['Value'])]
                
                df_closed = pd.concat([df_avg, df_avg.iloc[[0]]])
                
                # Grid (Concentric hexagons)
                grid_data = []
                steps = [max_val * 0.33, max_val * 0.66, max_val]
                for r in steps:
                    for i, a in enumerate(angles):
                        grid_data.append({'r_level': r, 'x': r * math.cos(a), 'y': r * math.sin(a), 'order': i})
                    grid_data.append({'r_level': r, 'x': r * math.cos(angles[0]), 'y': r * math.sin(angles[0]), 'order': 6})
                df_grid = pd.DataFrame(grid_data)
                
                # Axes (Lines from center to edges)
                axis_data = []
                for i, a in enumerate(angles):
                    axis_data.append({'axis': i, 'x': 0, 'y': 0, 'order': 0})
                    axis_data.append({'axis': i, 'x': max_val * math.cos(a), 'y': max_val * math.sin(a), 'order': 1})
                df_axes = pd.DataFrame(axis_data)
                
                # Text labels
                df_text = df_avg.copy()
                df_text['text_x'] = [(max_val + 25) * math.cos(angles[i]) for i in range(6)]
                df_text['text_y'] = [(max_val + 25) * math.sin(angles[i]) for i in range(6)]
                
                domain = [-max_val - 40, max_val + 40]
                
                chart_grid = alt.Chart(df_grid).mark_line(color='rgba(255,255,255,0.1)', strokeWidth=1).encode(
                    x=alt.X('x:Q', scale=alt.Scale(domain=domain), axis=None),
                    y=alt.Y('y:Q', scale=alt.Scale(domain=domain), axis=None),
                    detail='r_level:N',
                    order='order:Q'
                )
                
                chart_axes = alt.Chart(df_axes).mark_line(color='rgba(255,255,255,0.1)', strokeWidth=1).encode(
                    x='x:Q', y='y:Q', detail='axis:N', order='order:Q'
                )
                
                chart_area = alt.Chart(df_closed).mark_area(color='#4da6ff', opacity=0.3).encode(
                    x='x:Q', y='y:Q'
                )
                chart_line = alt.Chart(df_closed).mark_line(color='#4da6ff', strokeWidth=2).encode(
                    x='x:Q', y='y:Q'
                )
                chart_points = alt.Chart(df_avg).mark_point(color='#4da6ff', size=80, filled=True, opacity=1).encode(
                    x='x:Q', y='y:Q'
                )
                
                chart_labels = alt.Chart(df_text).mark_text(color='#e0e0e0', fontSize=13, fontWeight='bold').encode(
                    x='text_x:Q', y='text_y:Q', text='Stat:N'
                )
                chart_vals = alt.Chart(df_text).mark_text(color='#4da6ff', fontSize=12, dy=16).encode(
                    x='text_x:Q', y='text_y:Q', text='Value:Q'
                )
                
                final_chart = (chart_grid + chart_axes + chart_area + chart_line + chart_points + chart_labels + chart_vals).properties(height=350)
                final_chart = final_chart.configure_view(stroke=None)
                
                st.altair_chart(final_chart, use_container_width=True)

        st.divider()
        # Type Triangles Check
        TYPE_IDS = {
            "Normal": 1, "Fighting": 2, "Flying": 3, "Poison": 4, "Ground": 5, "Rock": 6,
            "Bug": 7, "Ghost": 8, "Steel": 9, "Fire": 10, "Water": 11, "Grass": 12,
            "Electric": 13, "Psychic": 14, "Ice": 15, "Dragon": 16, "Dark": 17, "Fairy": 18
        }
        TYPE_TRIANGLES = [
            ("Fire", "Grass", "Water"),
            ("Fire", "Steel", "Rock"),
            ("Grass", "Ground", "Poison"),
            ("Fighting", "Rock", "Flying")
        ]
        
        team_types = set()
        for p in team.pokemons:
            for t in get_pokemon_data(p.species)["types"]:
                team_types.add(t)
                
        triangles_found = [tri for tri in TYPE_TRIANGLES if all(t in team_types for t in tri)]
        
        if triangles_found:
            st.subheader("Perfect Type Triangles Detected")
            st.caption("*A perfect type triangle is a core where each type hits the next super-effectively and resists it in return.*")
            badges_html = ""
            for tri in triangles_found:
                badges_html += f"""
                <div style='display: inline-flex; align-items: center; background-color: rgba(128,128,128,0.1); border-radius: 8px; padding: 10px; margin-right: 15px; margin-bottom: 15px; border: 1px solid rgba(128,128,128,0.3); gap: 10px;'>
                    <img src='https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/types/generation-ix/scarlet-violet/{TYPE_IDS[tri[0]]}.png' width='75' />
                    <span style='font-size: 1.2em; font-weight: bold; color: rgba(255,255,255,0.5);'>➔</span>
                    <img src='https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/types/generation-ix/scarlet-violet/{TYPE_IDS[tri[1]]}.png' width='75' />
                    <span style='font-size: 1.2em; font-weight: bold; color: rgba(255,255,255,0.5);'>➔</span>
                    <img src='https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/types/generation-ix/scarlet-violet/{TYPE_IDS[tri[2]]}.png' width='75' />
                </div>
                """
            st.markdown(badges_html, unsafe_allow_html=True)
            st.divider()

        # Lead Combinations Matrix
        st.subheader("Lead Combinations Matrix")
        leads_matrix = evaluate_all_leads(stats_data)
        leads_html = build_leads_matrix_html(stats_data, leads_matrix)
        st.markdown(leads_html, unsafe_allow_html=True)
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
            headers = ["Type"] + [f"<img src='{d['Sprite']}' width='45' title='{d['Pokémon']}'>" for d in stats_data]
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
        st.markdown(build_synergy_html(synergy_data_def, is_defensive=True), unsafe_allow_html=True)
        st.write("<br>**Offensive Coverage**", unsafe_allow_html=True)
        st.markdown(build_synergy_html(synergy_data_off, is_defensive=False), unsafe_allow_html=True)


    else:
        st.info("Paste your team in the sidebar to see the breakdown.")
