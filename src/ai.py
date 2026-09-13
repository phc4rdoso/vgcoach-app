import google.generativeai as genai
import os
from typing import Dict, Any

def get_ai_vibe_check(team_data: str, regulation_desc: str, api_key: str) -> str:
    """
    Calls the Gemini API to perform a VGC Teambuilder analysis.
    """
    if not api_key:
        return "Please provide a Gemini API key to run the AI Vibe Check."
        
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3.1-pro-preview')
        
        prompt = f"""
        You are an expert Pokémon VGC Coach. Analyze the following team for the current regulation.
        
        Current Regulation Rules:
        {regulation_desc}
        
        Team Data:
        {team_data}
        
        Please provide:
        1. A brief overview of the team archetype (e.g., Rain, Trick Room, Balance).
        2. Glaring defensive weaknesses (e.g., weak to Ground or Fairy).
        3. A "Vibe Check" pointing out mis-optimizations (like inefficient EV spreads) or bad matchups.
        4. Suggestions for improvements.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error contacting AI: {str(e)}"
