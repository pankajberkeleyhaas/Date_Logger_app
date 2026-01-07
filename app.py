import streamlit as st
import pandas as pd
import os
import shutil
from datetime import datetime
import data_manager as dm
import chat_manager as cm
import ai_utils

# Page config
st.set_page_config(page_title="Date Logger - Personal AI Coach", page_icon="❤️", layout="wide")

# Initialize DBs
dm.init_db()
cm.init_chat_db()

# Custom CSS for aesthetics
st.markdown("""
    <style>
    .stApp {
        background-color: #f8f9fa;
    }
    .main-header {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #ff4b4b;
        text-align: center;
        font-weight: bold;
    }
    .stButton>button {
        background-color: #ff4b4b;
        color: white;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        border: none;
    }
    .stButton>button:hover {
        background-color: #ff6b6b;
    }
    </style>
""", unsafe_allow_html=True)

st.title("❤️ Date Logger & AI Coach")

# Session State for API Key
if 'gemini_api_key' not in st.session_state:
    st.session_state.gemini_api_key = ""

# Sidebar
with st.sidebar:
    st.header("🔑 AI Access")
    
    # API Key Input
    api_key_input = st.text_input("Gemini API Key", type="password", help="Get a key from Google AI Studio")
    if api_key_input:
        st.session_state.gemini_api_key = api_key_input
        st.success("API Key set!")
    
    st.divider()
    
    st.header("Navigation")
    # Updated Tabs
    tab_selection = st.radio("Go to", ["Log Date", "View History", "Chat Companion", "Settings"])

    if tab_selection == "Chat Companion":
        st.divider()
        st.subheader("Chat Sessions")
        if st.button("+ New Chat"):
            cm.create_session(f"Chat {datetime.now().strftime('%m-%d %H:%M')}")
            st.rerun()
        
        sessions = cm.get_sessions()
        if not sessions.empty:
            selected_session_id = st.radio(
                "Select Session", 
                sessions['id'].tolist(), 
                format_func=lambda x: sessions[sessions['id'] == x]['title'].values[0]
            )
        else:
            selected_session_id = None
            if st.button("Start First Chat"):
                cm.create_session("First Chat")
                st.rerun()

# --- TAB 1: LOG DATE ---
if tab_selection == "Log Date":
    st.header("📝 Log a New Date")
    
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Date", datetime.now())
            partner_name = st.text_input("Partner Name")
        with col2:
            social_media = st.text_input("Social Media (Optional)")
        
        st.subheader("Vibe Check / Attributes")
        # Fetch tags dynamically from DB
        tag_options = dm.get_custom_tags()
        tags = st.multiselect("Select attributes (Manage these in Settings):", tag_options)
        
        notes = st.text_area("Notes / Memories", height=150, placeholder="Write detailed notes here. The AI will use these to help you later!")
        
        st.subheader("📸 Media Upload")
        uploaded_files = st.file_uploader(
            "Upload Photos/Videos/Audio", 
            accept_multiple_files=True, 
            type=['png', 'jpg', 'jpeg', 'mp4', 'mov', 'mp3', 'wav']
        )
        
        submit_btn = st.form_submit_button("Save Entry")
        
        if submit_btn:
            if not partner_name:
                st.error("Partner Name is required!")
            else:
                media_list = []
                if uploaded_files:
                    for uploaded_file in uploaded_files:
                        # Determine type
                        file_type = uploaded_file.type.split('/')[0] # 'image', 'video', 'audio'
                        # Save file
                        save_path = os.path.join("media", uploaded_file.name)
                        with open(save_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        media_list.append((save_path, file_type))
                
                success, msg = dm.add_entry(date, partner_name, social_media, notes, tags, media_list)
                if success:
                    st.success(msg)
                else:
                    st.error(f"Error saving: {msg}")

# --- TAB 2: VIEW HISTORY ---
elif tab_selection == "View History":
    st.header("📜 History")
    
    df = dm.get_all_entries()
    
    if not df.empty:
        # Download options
        col1, col2 = st.columns([1, 4])
        with col1:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", csv, "date_log.csv", "text/csv")
        
        # Display Data
        st.dataframe(df.drop(columns=['id']), use_container_width=True)
        
        st.divider()
        st.subheader("Detailed View")
        
        for index, row in df.iterrows():
            with st.expander(f"{row['date']} - {row['partner_name']}"):
                # Display Tags
                if row['tags']:
                    tags_list = row['tags'].split(", ")
                    for tag in tags_list:
                        st.markdown(f"<span style='background-color:#ffe8e8; padding:3px 8px; border-radius:10px; margin-right:5px; color:#c92a2a; font-size:0.9em'>{tag}</span>", unsafe_allow_html=True)
                    st.write("") # Spacer

                st.write(f"**Social Media:** {row['social_media']}")
                st.write(f"**Notes:** {row['notes']}")
                
                media_items = dm.get_media_for_entry(row['id'])
                if media_items:
                    st.write("---")
                    cols = st.columns(3)
                    for i, (path, mtype) in enumerate(media_items):
                        with cols[i % 3]:
                            if mtype == 'image':
                                st.image(path)
                            elif mtype == 'video':
                                st.video(path)
                            elif mtype == 'audio':
                                st.audio(path)
    else:
        st.info("No entries yet. Go to 'Log Date' to add one!")

# --- TAB 3: CHAT COMPANION ---
elif tab_selection == "Chat Companion":
    st.header("💬 AI Dating Coach")
    st.markdown("Ask me anything about your dates! I'll use your logs and profile to give personalized advice.")
    
    if not st.session_state.gemini_api_key:
        st.warning("⚠️ Please enter your Gemini API Key in the Sidebar to enable AI features! Simple search is still active below.")

    if selected_session_id:
        # Display chat history
        messages = cm.get_messages(selected_session_id)
        for msg in messages:
            with st.chat_message(msg['role']):
                st.write(msg['content'])
        
        # Chat Input
        if prompt := st.chat_input("Ask about your dates..."):
            # 1. User Message
            cm.add_message(selected_session_id, "user", prompt)
            with st.chat_message("user"):
                st.write(prompt)
            
            # 2. Assistant Logic
            
            # Check for AI Key
            if st.session_state.gemini_api_key:
                context = dm.get_all_context_for_ai()
                user_profile = dm.get_user_profile()
                response = ai_utils.generate_ai_response(st.session_state.gemini_api_key, prompt, context, user_profile)
            else:
                # Fallback to Simple RAG
                results = dm.search_entries(prompt) 
                if not results.empty:
                    response = f"I found {len(results)} entries matching keywords:\n\n"
                    for i, row in results.iterrows():
                        response += f"- **{row['date']}** with **{row['partner_name']}** ({row['tags']}): {row['notes']}\n"
                else:
                    response = "I couldn't find any specific records matching that with simple search. Add an API Key for deeper insights!"

            # 3. Save & Display Assistant Message
            cm.add_message(selected_session_id, "assistant", response)
            with st.chat_message("assistant"):
                st.write(response)
                
    else:
        st.write("Create a new chat session to start!")

# --- TAB 4: SETTINGS ---
elif tab_selection == "Settings":
    st.header("⚙️ Settings & Profile")
    
    # 1. User Profile Section
    st.subheader("Your Profile")
    st.info("The AI will use this information to give you better, personalized advice.")
    
    current_profile = dm.get_user_profile()
    
    with st.form("profile_form"):
        p_name = st.text_input("Name", value=current_profile.get('name', ''))
        col_a, col_b = st.columns(2)
        with col_a:
            p_age = st.number_input("Age", min_value=18, max_value=100, value=current_profile.get('age', 25))
        with col_b:
            p_gender = st.selectbox("Gender", ["Male", "Female", "Non-binary", "Other", "Prefer not to say"], 
                                    index=0 if not current_profile.get('gender') else ["Male", "Female", "Non-binary", "Other", "Prefer not to say"].index(current_profile.get('gender')))
        
        p_goals = st.selectbox("Dating Goals", 
                               ["Long-term Relationship", "Casual Dating", "Marriage", "Friendship", "Figuring it out"],
                               index=0 if not current_profile.get('dating_goals') else ["Long-term Relationship", "Casual Dating", "Marriage", "Friendship", "Figuring it out"].index(current_profile.get('dating_goals')))
        
        p_interests = st.text_area("Interests / Hobbies", value=current_profile.get('interests', ''))
        
        if st.form_submit_button("Update Profile"):
            dm.update_user_profile(p_name, p_age, p_gender, p_goals, p_interests)
            st.success("Profile Updated!")
            st.rerun()

    st.divider()

    # 2. Tag Manager Section
    st.subheader("Unqiue Tags")
    st.write("Customize the attributes you see when logging a date.")
    
    current_tags = dm.get_custom_tags()
    
    # Add new tag
    c1, c2 = st.columns([3, 1])
    with c1:
        new_tag = st.text_input("New Tag Name")
    with c2:
        if st.button("Add Tag"):
            if new_tag:
                ok, msg = dm.add_custom_tag(new_tag)
                if ok: 
                    st.success(msg)
                    st.rerun()
                else:
                    st.warning(msg)
    
    # List and delete tags
    st.write("Current Tags:")
    # Display in chips with delete x
    for tag in current_tags:
        col_txt, col_del = st.columns([4, 1])
        col_txt.text(f"• {tag}")
        if col_del.button("❌", key=f"del_{tag}"):
            dm.delete_custom_tag(tag)
            st.rerun()
