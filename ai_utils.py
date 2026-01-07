import google.generativeai as genai
import streamlit as st

def get_model(api_key):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model
    except Exception as e:
        return None

def generate_ai_response(api_key, user_query, database_context):
    if not api_key:
        return "Please enter a Gemini API Key in the settings to use the AI features."
    
    model = get_model(api_key)
    if not model:
        return "Error configuring AI model. Check your API Key."

    system_prompt = f"""
    You are a helpful and empathetic implementation of a personal date logging assistant.
    Use the following logs of the user's past dates to answer their question. 
    Analyze patterns, preferences, and specific details from the logs.
    
    USER DATA LOGS:
    {database_context}
    
    Be concise but insightful. If the answer isn't in the logs, say so.
    """
    
    try:
        response = model.generate_content(f"{system_prompt}\n\nUSER QUESTION: {user_query}")
        return response.text
    except Exception as e:
        return f"AI Error: {str(e)}"
