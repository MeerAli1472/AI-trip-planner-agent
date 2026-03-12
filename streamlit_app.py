import streamlit as st
import requests
import datetime
from utils.chat_history import init_session, create_new_chat, add_message, get_messages
from utils.place_search_with_images import PlaceSearchWithImagesTool

BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="🌍 Travel Planner Agentic Application",
    page_icon="🌍",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.title("🌍 Travel Planner Agentic Application")

# Initialize session & tools
init_session()
place_image_tool = PlaceSearchWithImagesTool()
search_top_places = place_image_tool.tools_list[0]

# Sidebar chat
st.sidebar.title("💬 Chats")
if st.sidebar.button("➕ New Chat", key="new_chat_button"):
    create_new_chat()

for chat_id, chat_data in st.session_state.chats.items():
    title = chat_data["title"]
    if st.sidebar.button(title, key=f"chat_button_{chat_id}"):
        st.session_state.current_chat = chat_id

# Display chat history
messages = get_messages()
for msg in messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        st.chat_message("assistant").markdown(msg["content"], unsafe_allow_html=True)

# Chat input
user_input = st.chat_input("Plan a trip to Islamabad for 5 days...")

if user_input:
    add_message("user", user_input)
    st.chat_message("user").write(user_input)

    try:
        with st.spinner("Bot is thinking..."):
            payload = {
                "question": user_input,
                "thread_id": st.session_state.current_chat
            }
            response = requests.post(f"{BASE_URL}/query", json=payload)

        if response.status_code == 200:
            answer = response.json().get("answer", "No answer returned.")
            
            # Extract main place from input
            place_name = user_input.split("to")[-1].strip().split("for")[0].strip()
            if not place_name:
                place_name = "Islamabad"
            
            # Get top places with images
            with st.spinner(f"Finding attractions in {place_name}..."):
                places_info = search_top_places.run(place_name)
            
            # Display in chat message
            with st.chat_message("assistant"):
                # Display the AI travel plan
                st.markdown(f"""
# 🌍 AI Travel Plan

**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d at %H:%M')}  
**Created by:** Syed Meer Travel Agent

---

{answer}

""")
                
                # Display attractions with images
                if places_info and isinstance(places_info, list):
                    st.markdown(f"## 🏛️ Top Attractions in {place_name}")
                    
                    for place in places_info:
                        if "error" in place:
                            st.warning(place["error"])
                            continue
                            
                        # Create an expander for each attraction
                        with st.expander(f"📍 {place['title']}", expanded=True):
                            # Description
                            st.write(place['description'])
                            
                            # Images
                            if place.get('images') and place['images']:
                                # Filter out any non-URL strings or error messages
                                valid_images = [img for img in place['images'] 
                                              if isinstance(img, str) and img.startswith('http')]
                                
                                if valid_images:
                                    st.markdown("**📸 Images:**")
                                    
                                    # Display images in columns (max 3 per row)
                                    cols = st.columns(min(len(valid_images), 3))
                                    for idx, img_url in enumerate(valid_images[:3]):
                                        with cols[idx]:
                                            st.image(img_url, 
                                                    caption=f"{place['title']}",
                                                    use_container_width=True)
                                else:
                                    st.info("No images available for this attraction")
                            else:
                                st.info("No images available for this attraction")
                    
                    # Add a separator at the end
                    st.markdown("---")
                
                # Prepare the complete response for history
                complete_response = f"""
# 🌍 AI Travel Plan

**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d at %H:%M')}  
**Created by:** Syed Meer Travel Agent

---

{answer}

"""
                
                if places_info and isinstance(places_info, list):
                    complete_response += f"\n## 🏛️ Top Attractions in {place_name}\n\n"
                    for place in places_info:
                        if "error" not in place:
                            complete_response += f"### {place['title']}\n"
                            complete_response += f"{place['description']}\n\n"
                            if place.get('images') and place['images']:
                                valid_images = [img for img in place['images'] 
                                              if isinstance(img, str) and img.startswith('http')]
                                for img_url in valid_images[:3]:
                                    complete_response += f"![{place['title']}]({img_url})\n\n"
                            complete_response += "---\n\n"
                
                # Add to chat history
                add_message("assistant", complete_response)

        else:
            error_msg = f"Bot failed to respond: {response.text}"
            st.error(error_msg)
            add_message("assistant", error_msg)
            
    except Exception as e:
        error_msg = f"Response failed due to {e}"
        st.error(error_msg)
        add_message("assistant", error_msg)