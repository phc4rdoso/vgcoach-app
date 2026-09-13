import streamlit as st
from src.parser import parse_showdown_paste
import json

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

import pandas as pd
from src.pokeapi import get_pokemon_data, calculate_stat, get_nature_multiplier
from src.synergy import calculate_defensive_synergy, ALL_TYPES

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
                "Speed": actual_stats["Spe"],
                "HP": actual_stats["HP"],
                "Atk": actual_stats["Atk"],
                "Def": actual_stats["Def"],
                "SpA": actual_stats["SpA"],
                "SpD": actual_stats["SpD"],
                "Types": " / ".join(p_types)
            })
            
        # Display Stats Table
        df_stats = pd.DataFrame(stats_data).sort_values(by="Speed", ascending=False)
        st.dataframe(df_stats, use_container_width=True, hide_index=True)
        
        st.write("### Defensive Synergy Matrix")
        df_synergy = pd.DataFrame(synergy_data, index=pokemon_names).T
        
        def color_synergy(val):
            if val > 1: return 'background-color: #ffcccc' # weak (red)
            if val < 1 and val > 0: return 'background-color: #ccffcc' # resist (green)
            if val == 0: return 'background-color: #ccccff' # immune (blue)
            return ''
            
        st.dataframe(df_synergy.style.map(color_synergy), use_container_width=True)
        
        st.write("### AI Vibe Check")
        api_key = st.text_input("Enter your Gemini API Key", type="password")
        if st.button("Run Vibe Check"):
            if not api_key:
                st.error("Please provide an API key.")
            else:
                from src.ai import get_ai_vibe_check
                with st.spinner("Analyzing team..."):
                    vibe_result = get_ai_vibe_check(
                        team_data=str(stats_data),
                        regulation_desc=current_regulation.description,
                        api_key=api_key
                    )
                st.markdown(vibe_result)
    else:
        st.info("Paste your team and click 'Analyze Team' to see the breakdown.")
