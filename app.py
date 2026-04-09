import streamlit as st
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

# Load API keys from the .env file (for local testing)
load_dotenv()

# Streamlit Page Configuration
st.set_page_config(page_title="Smart Reminder AI", page_icon="🧠")

st.title("🧠 Smart AI Reminder System")
st.write("Welcome! Let the AI extract tasks, deadlines, and locations for you.")

# Retrieve the API key from Streamlit Secrets or local .env
API_KEY = os.getenv("GEMINI_API_KEY") 

if not API_KEY:
    try:
        # If deploying on Streamlit Cloud, it uses st.secrets
        API_KEY = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

if not API_KEY:
    st.warning("⚠️ No GEMINI_API_KEY found! Please set it in your .env locally or in Streamlit Secrets.")

else:
    # Configure Gemini API
    genai.configure(api_key=API_KEY)
    
    # Text input method
    user_text = st.text_input("Type your reminder (e.g., 'Remind me to buy milk tomorrow at 5 PM at Target'):")
    
    if st.button("Extract Reminder Details"):
        if user_text:
            with st.spinner("AI is analyzing text..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"""
                    You are an intelligent Natural Language Processing engine for a reminder app. 
                    Analyze the following user input and extract the core task, the specific time, and the location.
                    
                    Return ONLY a raw JSON dictionary without markdown formatting. Keep the answers concise.
                    Structure:
                    {{
                        "Task": "Description of the task",
                        "Time": "Extracted time or null if none",
                        "Location": "Extracted location or null if none"
                    }}
                    
                    User input: "{user_text}"
                    """
                    
                    response = model.generate_content(prompt)
                    
                    st.success("Analysis Complete!")
                    st.subheader("Extracted Data JSON:")
                    
                    # Try to parse and display as JSON natively in Streamlit
                    try:
                        result_dict = json.loads(response.text)
                        st.json(result_dict)
                    except json.JSONDecodeError:
                        # Fallback if AI returned something slightly misformatted
                        st.code(response.text, language="json")
                        
                except Exception as e:
                    st.error(f"Error communicating with AI API: {e}")
        else:
            st.error("Please enter a reminder first.")
            
    st.info("💡 Note on Voice Input: Since you are deploying on the cloud via Streamlit, hardware microphones (like PyAudio/SpeechRecognition) do not work because the code runs on a cloud server, not your browser. We will use Text for the NLP module instead for now!")

