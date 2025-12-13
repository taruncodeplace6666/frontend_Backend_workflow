import streamlit as st
import time

st.set_page_config(page_title="Contact Manager", page_icon="📇")

# Don't import db here - it will try to connect immediately
# Instead, import only when needed

if "initialized" not in st.session_state:
    st.session_state.initialized = False

if not st.session_state.initialized:
    st.title("Contact Manager")
    st.write("Click below to initialize the database")
    
    if st.button("Initialize"):
        try:
            # Import and initialize only when button is clicked
            from db import create_table_if_not_exists
            with st.spinner("Connecting to database..."):
                time.sleep(2)  # Give PostgreSQL extra time
                create_table_if_not_exists()
                st.session_state.initialized = True
                st.success("Database ready!")
                st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
            st.info("PostgreSQL might still be starting. Try again in 10 seconds.")
else:
    # Main app
    from db import get_all_contacts, create_contact, update_contact, delete_contact
    
    st.title("📇 Contact Manager")
    
    # Your app code here
    contacts = get_all_contacts()
    st.write(f"Contacts: {len(contacts)}")
