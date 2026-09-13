import streamlit as st
from src.parser import parse_showdown_paste
import json
import pandas as pd
from src.pokeapi import get_pokemon_data, calculate_stat, get_nature_multiplier
from src.synergy import calculate_defensive_synergy, ALL_TYPES
from src.regulations import get_all_regulation_names, get_regulation

st.set_page_config(page_title="VGCoach Teambuilder", page_icon="🎮", layout="wide")

st.title("🛡️ VGCoach - Teambuilding Assistant")
st.markdown("Paste your Pokémon Showdown team below to analyze it for the current VGC Regulation.")

# Regulation Selector
reg_names = get_all_regulation_names()
selected_reg_name = st.selectbox(
    "Select Current Regulation",
    reg_names,
    index=0
)

current_regulation = get_regulation(selected_reg_name)

st.info(f"**Current Meta - {current_regulation.name}:** {current_regulation.description}")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Input Team")
    paste_input = st.text_area("Showdown Paste", height=400, placeholder="Incineroar @ Sitrus Berry\nAbility: Intimidate\nLevel: 50\n...")
    
    if st.button("Analyze Team"):
        if paste_input:
            st.session_state['team'] = parse_showdown_paste(paste_input)
        else:
            st.warning("Please enter a valid Showdown paste.")

with col2:
    st.subheader("Team Analysis")
    
    if 'team' in st.session_state:
        team = st.session_state['team']
        st.success(f"Successfully parsed {len(team.pokemons)} Pokémon!")
        
        st.write("### Speed Tiers & Stats")
        stats_data = []
        synergy_data = {t: [] for t in ALL_TYPES}
        pokemon_names = []
        
        for p in team.pokemons:
            api_data = get_pokemon_data(p.species)
            base_stats = api_data["stats"]
            p_types = api_data["types"]
            sprite_url = api_data.get("sprite", "")
            
            pokemon_names.append(p.species)
            
            # Synergy calculation
            defensive_mults = calculate_defensive_synergy(p_types)
            for t, mult in defensive_mults.items():
                synergy_data[t].append(mult)
            
            # Stat calculation
            actual_stats = {}
            for stat in ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]:
                is_hp = (stat == "HP")
                base = base_stats.get(stat, 100)
                ev = p.evs.get(stat, 0)
                iv = p.ivs.get(stat, 31)
                nature_mult = get_nature_multiplier(p.nature, stat)
                actual = calculate_stat(base, ev, iv, p.level, is_hp, nature_mult)
                actual_stats[stat] = actual
                
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
                            <h3 style="margin: 0; font-size: 1.2em;">{pd_data['Pokémon']}</h3>
                            <div style="font-size: 0.9em; opacity: 0.8;">@ {pd_data['Item']}</div>
                        </div>
                    </div>
                    <div style="font-size: 0.9em; line-height: 1.6; margin-bottom: 12px;">
                        <div><b>Ability:</b> {pd_data['Ability']}</div>
                        <div><b>Tera Type:</b> {pd_data['Tera']}</div>
                        <div><b>Nature:</b> {pd_data['Nature']}</div>
                        <div style="color: #4da6ff; font-weight: 500;"><b>EVs:</b> {ev_string}</div>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.85em;">
                        {moves_html}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
        # Composition Warnings
        physical_count = 0
        special_count = 0
        for d in stats_data:
            if d['Atk'] > d['SpA'] + 15:
                physical_count += 1
            elif d['SpA'] > d['Atk'] + 15:
                special_count += 1
                
        if physical_count >= 4 and special_count <= 1:
            st.warning(f"⚠️ **Unbalanced Offense:** Your team is heavily skewed towards Physical attackers ({physical_count} Physical vs {special_count} Special). You might struggle against teams with Intimidate or high Physical Defense.")
        elif special_count >= 4 and physical_count <= 1:
            st.warning(f"⚠️ **Unbalanced Offense:** Your team is heavily skewed towards Special attackers ({special_count} Special vs {physical_count} Physical). You might struggle against Assault Vest users or high Special Defense walls like Snarl users.")
        else:
            st.success(f"✅ **Balanced Offense:** Your team has a healthy mix of Physical ({physical_count}) and Special ({special_count}) attackers.")
            
        # 2. Horizontal Bar Chart for Team's Average Stats
        st.write("### Team Average Stats")
        avg_stats = {
            "HP": sum(d["HP"] for d in stats_data) / len(stats_data),
            "Atk": sum(d["Atk"] for d in stats_data) / len(stats_data),
            "Def": sum(d["Def"] for d in stats_data) / len(stats_data),
            "SpA": sum(d["SpA"] for d in stats_data) / len(stats_data),
            "SpD": sum(d["SpD"] for d in stats_data) / len(stats_data),
            "Speed": sum(d["Speed"] for d in stats_data) / len(stats_data),
        }
        df_avg = pd.DataFrame(list(avg_stats.items()), columns=["Stat", "Average"])
        st.bar_chart(df_avg.set_index("Stat"), horizontal=True)

        # 3. Defensive Synergy Matrix
        st.write("### Defensive Synergy Matrix")
        
        # Formatting for the cells
        def format_synergy(val):
            if val == 2.0: return '2x'
            if val == 4.0: return '4x'
            if val == 0.5: return '1/2'
            if val == 0.25: return '1/4'
            if val == 0.0: return 'immune'
            return ''
            
        df_synergy = pd.DataFrame(synergy_data, index=pokemon_names).T
        df_synergy_formatted = df_synergy.applymap(format_synergy)
        
        def color_synergy_styled(val):
            if val in ['2x', '4x']:
                return 'background-color: rgba(200, 50, 50, 0.4); color: inherit; font-weight: bold;'
            if val in ['1/2', '1/4']:
                return 'background-color: rgba(50, 150, 50, 0.4); color: inherit; font-weight: bold;'
            if val == 'immune':
                return 'background-color: rgba(100, 100, 100, 0.4); color: inherit; font-weight: bold;'
            return 'color: transparent;' # neutral 1x (hide text)
            
        st.dataframe(df_synergy_formatted.style.map(color_synergy_styled), use_container_width=True)
        
        # 4. AI Vibe Check
        st.write("### AI Vibe Check")
        api_key = st.text_input("Enter your Gemini API Key", type="password", value="REMOVED_SECRET")
        if st.button("Run Vibe Check"):
            if not api_key:
                st.error("Please provide an API key.")
            else:
                from src.ai import get_ai_vibe_check
                with st.spinner("Analyzing team..."):
                    vibe_result = get_ai_vibe_check(
                        team_data=str([{k:v for k,v in d.items() if k != 'Sprite'} for d in stats_data]),
                        regulation_desc=current_regulation.description,
                        api_key=api_key
                    )
                st.markdown(vibe_result)
    else:
        st.info("Paste your team and click 'Analyze Team' to see the breakdown.")
