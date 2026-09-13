import streamlit as st
from src.parser import parse_showdown_paste
import json

st.set_page_config(page_title="VGCoach Teambuilder", page_icon="🎮", layout="wide")

st.title("🛡️ VGCoach - Teambuilding Assistant")
st.markdown("Paste your Pokémon Showdown team below to analyze it for the current VGC Regulation.")

# Regulation Selector
regulation = st.selectbox(
    "Select Current Regulation",
    ["Regulation H", "Regulation G", "Regulation F"],
    index=0
)

st.write(f"**Current Meta:** {regulation} (Analysis will be tailored to this format).")

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
        
        # Display basic parsed info as a placeholder
        for p in team.pokemons:
            with st.expander(f"{p.species} @ {p.item or 'No Item'}"):
                st.json(p.model_dump())
                
        st.info("Next steps: Type Synergy Matrix, Speed Tiers, and AI Vibe Check will be implemented here.")
    else:
        st.info("Paste your team and click 'Analyze Team' to see the breakdown.")
