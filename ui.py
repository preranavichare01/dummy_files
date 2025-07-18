import streamlit as st
import pandas as pd
import chromadb
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from datetime import datetime
import matplotlib.pyplot as plt
from collections import Counter
import re
import matplotlib.pyplot as plt
 
# --- Main function for the chatbot view ---
def show_chatbot_view():
    # --- START HTML/CSS BLOCK FOR HEADER ---
    header_html_content = """
<style>
        @keyframes fadeInSlide {
            0% {
                opacity: 0;
                transform: translateY(-20px);
            }
            100% {
                opacity: 1;
                transform: translateY(0);
            }
        }
        .animated-title {
            font-size: 2.5em;
            font-weight: bold;
            text-align: center;
            color: white;
            animation: fadeInSlide 1s ease-out forwards;
            margin-bottom: 0.5em;
        }
        .chat-bubble {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 16px;
            margin: 8px 0;
            font-size: 16px;
            line-height: 1.4;
            color: #000;
            background-color: #ffffffcc;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            display: inline-block;
        }
        .chat-left {
            text-align: left;
            justify-content: flex-start;
        }
        .chat-right {
            text-align: right;
            justify-content: flex-end;
        }
        /* New styles for filter labels */
        .filter-header {
            color: #FFD700;  /* Gold color */
            font-weight: 600;
            margin-bottom: 0.25em;
        }
        /* Make the expander title text white */
        div[role="button"][data-testid="stExpanderHeader"] > div:first-child {
            color: white !important;
            font-weight: 600;
        }
</style>
 
<div class="animated-title">💬 Job Market Chatbot</div>
<hr style='border: 1px solid #FFD700; margin-top: -10px;'>
    """
    st.markdown(header_html_content, unsafe_allow_html=True)
    # --- END HTML/CSS BLOCK FOR HEADER ---
 
 
    # Initialize session state for messages
    if "messages" not in st.session_state:
        st.session_state.messages = []
 
    # Load the Excel data file
    df = None # Initialize df to None
    try:
        df = pd.read_excel("data/combined_jobs.xlsx")
        st.sidebar.success("✅ Excel data loaded successfully.")
        st.sidebar.write(f"DataFrame shape: {df.shape}")
        st.sidebar.write(f"DataFrame columns: {df.columns.tolist()}")
        if 'Skills' not in df.columns or 'Location' not in df.columns or 'Posted On' not in df.columns:
            st.sidebar.error("❌ Warning: 'Skills', 'Location', or 'Posted On' columns missing from Excel file.")
            st.dataframe(df.head()) # Show head of dataframe for inspection
    except Exception as e:
        st.error(f"❌ Error loading data: {e}. Please ensure 'updated_dataframe.xlsx' exists in the 'data' folder and is accessible.")
        return # Exit if data cannot be loaded
 
    # Connect to ChromaDB vector database with embedding function
    collection = None # Initialize collection to None
from chromadb.config import Settings
try:
    client = chromadb.PersistentClient(path="chroma_db")
    collection = client.get_collection("job_collection")
    results = collection.get()
    docs = results["documents"]
    metas = results["metadatas"]
    st.success("✅ Connected to ChromaDB.")
except Exception as e:
    st.error(f"❌ Could not connect to ChromaDB: {e}")
    st.stop()  # Stop execution if ChromaDB fails
        # collection remains None, which triggers fallback for filters and search
 
 
    # --- START FILTER DATA EXTRACTION (Crucial for active filters) ---
    all_metadatas_for_filters = [] # This will hold data for populating filter options
 
    if collection:
        try:
            # Try to get metadatas from ChromaDB
            chroma_metadatas = collection.get(include=["metadatas"], limit=100000)["metadatas"] # Increased limit for more data
            if chroma_metadatas:
                all_metadatas_for_filters = chroma_metadatas
                st.sidebar.info(f"Loaded {len(all_metadatas_for_filters)} metadatas from ChromaDB for filters.")
            else:
                st.sidebar.info("💡 Vector database collection is empty. Populating filters from Excel data.")
                all_metadatas_for_filters = df.to_dict(orient='records') # Fallback to df
        except Exception as e:
            st.sidebar.error(f"❌ Error retrieving data from ChromaDB collection: {e}. Populating filters from Excel data.")
            all_metadatas_for_filters = df.to_dict(orient='records') # Fallback to df in case of collection query error
    else:
        # If ChromaDB connection failed entirely, use df data
        st.sidebar.info("Using Excel data for filters (ChromaDB not active).")
        all_metadatas_for_filters = df.to_dict(orient='records')
 
    # --- Debugging: Check the content of all_metadatas_for_filters ---
    if not all_metadatas_for_filters:
        st.sidebar.error("❌ `all_metadatas_for_filters` is empty. Filters will be disabled. Check Excel data or ChromaDB collection.")
        # You might want to display raw data if it's empty to aid debugging
        # st.dataframe(df)
 
    # Now, extract options from all_metadatas_for_filters (which comes from ChromaDB or df)
    all_dates = sorted(set(meta.get("Posted On", "N/A") for meta in all_metadatas_for_filters if meta.get("Posted On")))
    all_skills = sorted(set(
        skill.strip()
        for meta in all_metadatas_for_filters
        for skill_str in [str(meta.get("Skills", ""))] # Ensure it's a string, even if original is None/NaN
        for skill in skill_str.split(',') # Split the string
        if skill.strip() and skill.strip().lower() not in ['nan', 'none'] # Filter out "nan" or "none" strings
    ))
    all_locations = sorted(set(
        location.strip()
        for meta in all_metadatas_for_filters
        for location in [str(meta.get("Location", ""))] # Ensure string conversion
        if location.strip() and location.strip().lower() not in ['nan', 'none']
    ))
 
 
    available_dates = []
    for d_str in all_dates:
        try:
            available_dates.append(datetime.strptime(d_str, "%d %b %Y").date())
        except ValueError:
            # Handle cases where date string is not in expected format
            continue
    available_dates = sorted(list(set(available_dates))) # Ensure uniqueness and sort again
 
    # Ensure min/max dates are always available for st.date_input
    if not available_dates:
        today = datetime.today().date()
        available_dates = [today, today]
        st.sidebar.warning("⚠️ No valid dates found for filter. Defaulting to today's date range.")
    else:
        # If only one date is available, use it for both min and max
        if len(available_dates) == 1:
            available_dates.append(available_dates[0]) # Duplicate the single date
 
    # --- Debugging: Check extracted filter options ---
    st.sidebar.write(f"Extracted Skills count: {len(all_skills)}")
    st.sidebar.write(f"Extracted Locations count: {len(all_locations)}")
    st.sidebar.write(f"Extracted Dates count: {len(available_dates)}")
 
    # --- END FILTER DATA EXTRACTION ---
 
 
    # Filters inside an expander with colored labels
    with st.expander("🔍 Filter Jobs", expanded=True):
        st.markdown('<div class="filter-header">📅 Posted Between</div>', unsafe_allow_html=True)
        # Ensure the date range value is a tuple of two dates
        current_date_value = (min(available_dates), max(available_dates))
 
        selected_date_range = st.date_input(
            "",
            value=current_date_value,
            min_value=min(available_dates),
            max_value=max(available_dates),
            key="chatbot_date_range" # ADDED UNIQUE KEY
        )
 
        st.markdown('<div class="filter-header">🛠️ Skills</div>', unsafe_allow_html=True)
        selected_skills = st.multiselect("", options=all_skills, key="filter_skills") # ADDED UNIQUE KEY
 
        st.markdown('<div class="filter-header">📍 Location</div>', unsafe_allow_html=True)
        selected_locations = st.multiselect("", options=all_locations, key="filter_locations") # ADDED UNIQUE KEY
 
    st.markdown("---")
 
    # Display previous chat messages with bubbles aligned left/right
    for message in st.session_state.messages:
        alignment = "chat-right" if message["role"] == "user" else "chat-left"
        with st.container():
            st.markdown(f"""
<div class="{alignment}">
<div class="chat-bubble">{message['content']}</div>
</div>
            """, unsafe_allow_html=True)
 
    # User chat input
    if prompt := st.chat_input("Ask about job requirements..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message immediately
        with st.container():
            st.markdown(f"""
<div class="chat-right">
<div class="chat-bubble">{prompt}</div>
</div>
            """, unsafe_allow_html=True)
 
        with st.spinner("🤖 Analyzing job listings..."):
            try:
                relevant_jobs = []
 
                if collection:
                    results = collection.query(query_texts=[prompt], n_results=50) # Query for more results to filter down
                    if results and results["documents"] and results["metadatas"] and results["documents"][0] and results["metadatas"][0]:
                        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                            try:
                                posted_on = datetime.strptime(meta.get("Posted On", ""), "%d %b %Y").date()
                            except ValueError:
                                posted_on = None # Invalid date string
 
                            # Filtering logic
                            date_match = True
                            if selected_date_range and len(selected_date_range) == 2:
                                if posted_on:
                                    date_match = (selected_date_range[0] <= posted_on <= selected_date_range[1])
                                else:
                                    date_match = False # No valid date in metadata
 
                            skills_match = not selected_skills or any(
                                skill.strip() in selected_skills for skill in str(meta.get("Skills", "")).split(",") if skill.strip()
                            )
                            location_match = not selected_locations or (meta.get("Location", "").strip() in selected_locations)
 
                            if date_match and skills_match and location_match:
                                relevant_jobs.append({
                                    "title": meta.get("Job Title", "N/A"),
                                    "skills": meta.get("Skills", "N/A"),
                                    "location": meta.get("Location", "N/A"),
                                    "experience": meta.get("Experience Level", "N/A"),
                                    "description": doc[:500] if doc else "N/A", # Truncate description for brevity
                                    "posted_on": meta.get("Posted On", "N/A"),
                                    "link": meta.get("Link", "#"),
                                })
                                if len(relevant_jobs) >= 5: # Limit results displayed from search
                                    break
                    else:
                        st.info("No relevant results found in the vector database matching your query after filtering.")
                else:
                    # Fallback search in dataframe text if ChromaDB is not available or failed
                    st.info("Using fallback search (Excel data) as vector database is not active.")
                    for _, row in df.iterrows():
                        # Basic keyword matching for fallback
                        full_desc = str(row.get("Full Description", ""))
                        job_title = str(row.get("Job Title", ""))
                        skills_str = str(row.get("Skills", ""))
 
                        if prompt.lower() in full_desc.lower() or \
                           prompt.lower() in job_title.lower() or \
                           prompt.lower() in skills_str.lower():
 
                            # Apply filters for fallback (ensure they match the vector DB logic)
                            try:
                                posted_on_df = datetime.strptime(str(row.get("Posted On", "")), "%d %b %Y").date()
                            except ValueError:
                                posted_on_df = None
 
                            date_match_df = True
                            if selected_date_range and len(selected_date_range) == 2:
                                if posted_on_df:
                                    date_match_df = (selected_date_range[0] <= posted_on_df <= selected_date_range[1])
                                else:
                                    date_match_df = False
 
                            skills_match_df = not selected_skills or any(
                                skill.strip() in selected_skills for skill in skills_str.split(",") if skill.strip()
                            )
                            location_match_df = not selected_locations or (str(row.get("Location", "")).strip() in selected_locations)
 
                            if date_match_df and skills_match_df and location_match_df:
                                relevant_jobs.append({
                                    "title": row.get("Job Title", "N/A"),
                                    "skills": row.get("Skills", "N/A"),
                                    "location": row.get("Location", "N/A"),
                                    "experience": row.get("Experience Level", "N/A"),
                                    "description": full_desc[:500],
                                    "posted_on": row.get("Posted On", "N/A"),
                                    "link": row.get("Link", "#")
                                })
 
                                if len(relevant_jobs) >= 5: # Limit results for fallback
                                    break
 
                # Prepare chatbot response with relevant job info
                if relevant_jobs:
                    response = "Here are some relevant jobs I found:\n\n"
                    # Limit to top 3 for cleaner display in chat
                    for i, job in enumerate(relevant_jobs[:3], 1):
                        response += f"{i}. **{job['title']}**\n"
                        response += f"   - 📍 Location: {job['location']}\n"
                        response += f"   - 🛠️ Skills: {job['skills']}\n"
                        response += f"   - 🧰 Experience: {job['experience']}\n"
                        response += f"   - 🗓️ Posted On: {job.get('posted_on', 'N/A')}\n"
                        response += f"   - 🔗 [Job Link]({job.get('link', '#')})\n\n"
                else:
                    response = "❌ I couldn't find any relevant job listings for your query with the current filters. Please try rephrasing or adjusting the filters."
 
            except Exception as e:
                response = f"⚠️ Sorry, I encountered an error while searching for jobs: {str(e)}"
                st.exception(e) # Display the full traceback for debugging
 
        st.session_state.messages.append({"role": "assistant", "content": response})
        # Display assistant message
        with st.container():
            st.markdown(f"""
<div class="chat-left">
<div class="chat-bubble">{response}</div>
</div>
            """, unsafe_allow_html=True)
 
        # Rerun the script to update the chat UI and ensure input is cleared.
        st.experimental_rerun()
 
# --- Entry point for the Streamlit app ---
if __name__ == "__main__":
    show_chatbot_view()
 
 
 
 
 
 
 
 import streamlit as st
import pandas as pd
import chromadb
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from datetime import datetime
import matplotlib.pyplot as plt
from collections import Counter
import re
import matplotlib.pyplot as plt
 
# --- Main function for the chatbot view ---
def show_chatbot_view():
    # --- START HTML/CSS BLOCK FOR HEADER ---
    header_html_content = """
<style>
        @keyframes fadeInSlide {
            0% {
                opacity: 0;
                transform: translateY(-20px);
            }
            100% {
                opacity: 1;
                transform: translateY(0);
            }
        }
        .animated-title {
            font-size: 2.5em;
            font-weight: bold;
            text-align: center;
            color: white;
            animation: fadeInSlide 1s ease-out forwards;
            margin-bottom: 0.5em;
        }
        .chat-bubble {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 16px;
            margin: 8px 0;
            font-size: 16px;
            line-height: 1.4;
            color: #000;
            background-color: #ffffffcc;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            display: inline-block;
        }
        .chat-left {
            text-align: left;
            justify-content: flex-start;
        }
        .chat-right {
            text-align: right;
            justify-content: flex-end;
        }
        /* New styles for filter labels */
        .filter-header {
            color: #FFD700;  /* Gold color */
            font-weight: 600;
            margin-bottom: 0.25em;
        }
        /* Make the expander title text white */
        div[role="button"][data-testid="stExpanderHeader"] > div:first-child {
            color: white !important;
            font-weight: 600;
        }
</style>
 
<div class="animated-title">💬 Job Market Chatbot</div>
<hr style='border: 1px solid #FFD700; margin-top: -10px;'>
    """
    st.markdown(header_html_content, unsafe_allow_html=True)
    # --- END HTML/CSS BLOCK FOR HEADER ---
 
 
    # Initialize session state for messages
    if "messages" not in st.session_state:
        st.session_state.messages = []
 
    # Load the Excel data file
    df = None # Initialize df to None
    try:
        df = pd.read_excel("data/combined_jobs.xlsx")
        st.sidebar.success("✅ Excel data loaded successfully.")
        st.sidebar.write(f"DataFrame shape: {df.shape}")
        st.sidebar.write(f"DataFrame columns: {df.columns.tolist()}")
        if 'Skills' not in df.columns or 'Location' not in df.columns or 'Posted On' not in df.columns:
            st.sidebar.error("❌ Warning: 'Skills', 'Location', or 'Posted On' columns missing from Excel file.")
            st.dataframe(df.head()) # Show head of dataframe for inspection
    except Exception as e:
        st.error(f"❌ Error loading data: {e}. Please ensure 'updated_dataframe.xlsx' exists in the 'data' folder and is accessible.")
        return # Exit if data cannot be loaded
 
    # Connect to ChromaDB vector database with embedding function
    collection = None # Initialize collection to None
from chromadb.config import Settings
try:
    client = chromadb.PersistentClient(path="chroma_db")
    collection = client.get_collection("job_collection")
    results = collection.get()
    docs = results["documents"]
    metas = results["metadatas"]
    st.success("✅ Connected to ChromaDB.")
except Exception as e:
    st.error(f"❌ Could not connect to ChromaDB: {e}")
    st.stop()  # Stop execution if ChromaDB fails
        # collection remains None, which triggers fallback for filters and search
 
 
    # --- START FILTER DATA EXTRACTION (Crucial for active filters) ---
    all_metadatas_for_filters = [] # This will hold data for populating filter options
 
    if collection:
        try:
            # Try to get metadatas from ChromaDB
            chroma_metadatas = collection.get(include=["metadatas"], limit=100000)["metadatas"] # Increased limit for more data
            if chroma_metadatas:
                all_metadatas_for_filters = chroma_metadatas
                st.sidebar.info(f"Loaded {len(all_metadatas_for_filters)} metadatas from ChromaDB for filters.")
            else:
                st.sidebar.info("💡 Vector database collection is empty. Populating filters from Excel data.")
                all_metadatas_for_filters = df.to_dict(orient='records') # Fallback to df
        except Exception as e:
            st.sidebar.error(f"❌ Error retrieving data from ChromaDB collection: {e}. Populating filters from Excel data.")
            all_metadatas_for_filters = df.to_dict(orient='records') # Fallback to df in case of collection query error
    else:
        # If ChromaDB connection failed entirely, use df data
        st.sidebar.info("Using Excel data for filters (ChromaDB not active).")
        all_metadatas_for_filters = df.to_dict(orient='records')
 
    # --- Debugging: Check the content of all_metadatas_for_filters ---
    if not all_metadatas_for_filters:
        st.sidebar.error("❌ `all_metadatas_for_filters` is empty. Filters will be disabled. Check Excel data or ChromaDB collection.")
        # You might want to display raw data if it's empty to aid debugging
        # st.dataframe(df)
 
    # Now, extract options from all_metadatas_for_filters (which comes from ChromaDB or df)
    all_dates = sorted(set(meta.get("Posted On", "N/A") for meta in all_metadatas_for_filters if meta.get("Posted On")))
    all_skills = sorted(set(
        skill.strip()
        for meta in all_metadatas_for_filters
        for skill_str in [str(meta.get("Skills", ""))] # Ensure it's a string, even if original is None/NaN
        for skill in skill_str.split(',') # Split the string
        if skill.strip() and skill.strip().lower() not in ['nan', 'none'] # Filter out "nan" or "none" strings
    ))
    all_locations = sorted(set(
        location.strip()
        for meta in all_metadatas_for_filters
        for location in [str(meta.get("Location", ""))] # Ensure string conversion
        if location.strip() and location.strip().lower() not in ['nan', 'none']
    ))
 
 
    available_dates = []
    for d_str in all_dates:
        try:
            available_dates.append(datetime.strptime(d_str, "%d %b %Y").date())
        except ValueError:
            # Handle cases where date string is not in expected format
            continue
    available_dates = sorted(list(set(available_dates))) # Ensure uniqueness and sort again
 
    # Ensure min/max dates are always available for st.date_input
    if not available_dates:
        today = datetime.today().date()
        available_dates = [today, today]
        st.sidebar.warning("⚠️ No valid dates found for filter. Defaulting to today's date range.")
    else:
        # If only one date is available, use it for both min and max
        if len(available_dates) == 1:
            available_dates.append(available_dates[0]) # Duplicate the single date
 
    # --- Debugging: Check extracted filter options ---
    st.sidebar.write(f"Extracted Skills count: {len(all_skills)}")
    st.sidebar.write(f"Extracted Locations count: {len(all_locations)}")
    st.sidebar.write(f"Extracted Dates count: {len(available_dates)}")
 
    # --- END FILTER DATA EXTRACTION ---
 
 
    # Filters inside an expander with colored labels
    with st.expander("🔍 Filter Jobs", expanded=True):
        st.markdown('<div class="filter-header">📅 Posted Between</div>', unsafe_allow_html=True)
        # Ensure the date range value is a tuple of two dates
        current_date_value = (min(available_dates), max(available_dates))
 
        selected_date_range = st.date_input(
            "",
            value=current_date_value,
            min_value=min(available_dates),
            max_value=max(available_dates),
            key="chatbot_date_range" # ADDED UNIQUE KEY
        )
 
        st.markdown('<div class="filter-header">🛠️ Skills</div>', unsafe_allow_html=True)
        selected_skills = st.multiselect("", options=all_skills, key="filter_skills") # ADDED UNIQUE KEY
 
        st.markdown('<div class="filter-header">📍 Location</div>', unsafe_allow_html=True)
        selected_locations = st.multiselect("", options=all_locations, key="filter_locations") # ADDED UNIQUE KEY
 
    st.markdown("---")
 
    # Display previous chat messages with bubbles aligned left/right
    for message in st.session_state.messages:
        alignment = "chat-right" if message["role"] == "user" else "chat-left"
        with st.container():
            st.markdown(f"""
<div class="{alignment}">
<div class="chat-bubble">{message['content']}</div>
</div>
            """, unsafe_allow_html=True)
 
    # User chat input
    if prompt := st.chat_input("Ask about job requirements..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message immediately
        with st.container():
            st.markdown(f"""
<div class="chat-right">
<div class="chat-bubble">{prompt}</div>
</div>
            """, unsafe_allow_html=True)
 
        with st.spinner("🤖 Analyzing job listings..."):
            try:
                relevant_jobs = []
 
                if collection:
                    results = collection.query(query_texts=[prompt], n_results=50) # Query for more results to filter down
                    if results and results["documents"] and results["metadatas"] and results["documents"][0] and results["metadatas"][0]:
                        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                            try:
                                posted_on = datetime.strptime(meta.get("Posted On", ""), "%d %b %Y").date()
                            except ValueError:
                                posted_on = None # Invalid date string
 
                            # Filtering logic
                            date_match = True
                            if selected_date_range and len(selected_date_range) == 2:
                                if posted_on:
                                    date_match = (selected_date_range[0] <= posted_on <= selected_date_range[1])
                                else:
                                    date_match = False # No valid date in metadata
 
                            skills_match = not selected_skills or any(
                                skill.strip() in selected_skills for skill in str(meta.get("Skills", "")).split(",") if skill.strip()
                            )
                            location_match = not selected_locations or (meta.get("Location", "").strip() in selected_locations)
 
                            if date_match and skills_match and location_match:
                                relevant_jobs.append({
                                    "title": meta.get("Job Title", "N/A"),
                                    "skills": meta.get("Skills", "N/A"),
                                    "location": meta.get("Location", "N/A"),
                                    "experience": meta.get("Experience Level", "N/A"),
                                    "description": doc[:500] if doc else "N/A", # Truncate description for brevity
                                    "posted_on": meta.get("Posted On", "N/A"),
                                    "link": meta.get("Link", "#"),
                                })
                                if len(relevant_jobs) >= 5: # Limit results displayed from search
                                    break
                    else:
                        st.info("No relevant results found in the vector database matching your query after filtering.")
                else:
                    # Fallback search in dataframe text if ChromaDB is not available or failed
                    st.info("Using fallback search (Excel data) as vector database is not active.")
                    for _, row in df.iterrows():
                        # Basic keyword matching for fallback
                        full_desc = str(row.get("Full Description", ""))
                        job_title = str(row.get("Job Title", ""))
                        skills_str = str(row.get("Skills", ""))
 
                        if prompt.lower() in full_desc.lower() or \
                           prompt.lower() in job_title.lower() or \
                           prompt.lower() in skills_str.lower():
 
                            # Apply filters for fallback (ensure they match the vector DB logic)
                            try:
                                posted_on_df = datetime.strptime(str(row.get("Posted On", "")), "%d %b %Y").date()
                            except ValueError:
                                posted_on_df = None
 
                            date_match_df = True
                            if selected_date_range and len(selected_date_range) == 2:
                                if posted_on_df:
                                    date_match_df = (selected_date_range[0] <= posted_on_df <= selected_date_range[1])
                                else:
                                    date_match_df = False
 
                            skills_match_df = not selected_skills or any(
                                skill.strip() in selected_skills for skill in skills_str.split(",") if skill.strip()
                            )
                            location_match_df = not selected_locations or (str(row.get("Location", "")).strip() in selected_locations)
 
                            if date_match_df and skills_match_df and location_match_df:
                                relevant_jobs.append({
                                    "title": row.get("Job Title", "N/A"),
                                    "skills": row.get("Skills", "N/A"),
                                    "location": row.get("Location", "N/A"),
                                    "experience": row.get("Experience Level", "N/A"),
                                    "description": full_desc[:500],
                                    "posted_on": row.get("Posted On", "N/A"),
                                    "link": row.get("Link", "#")
                                })
 
                                if len(relevant_jobs) >= 5: # Limit results for fallback
                                    break
 
                # Prepare chatbot response with relevant job info
                if relevant_jobs:
                    response = "Here are some relevant jobs I found:\n\n"
                    # Limit to top 3 for cleaner display in chat
                    for i, job in enumerate(relevant_jobs[:3], 1):
                        response += f"{i}. **{job['title']}**\n"
                        response += f"   - 📍 Location: {job['location']}\n"
                        response += f"   - 🛠️ Skills: {job['skills']}\n"
                        response += f"   - 🧰 Experience: {job['experience']}\n"
                        response += f"   - 🗓️ Posted On: {job.get('posted_on', 'N/A')}\n"
                        response += f"   - 🔗 [Job Link]({job.get('link', '#')})\n\n"
                else:
                    response = "❌ I couldn't find any relevant job listings for your query with the current filters. Please try rephrasing or adjusting the filters."
 
            except Exception as e:
                response = f"⚠️ Sorry, I encountered an error while searching for jobs: {str(e)}"
                st.exception(e) # Display the full traceback for debugging
 
        st.session_state.messages.append({"role": "assistant", "content": response})
        # Display assistant message
        with st.container():
            st.markdown(f"""
<div class="chat-left">
<div class="chat-bubble">{response}</div>
</div>
            """, unsafe_allow_html=True)
 
        # Rerun the script to update the chat UI and ensure input is cleared.
        st.experimental_rerun()
 
# --- Entry point for the Streamlit app ---
if __name__ == "__main__":
    show_chatbot_view()
