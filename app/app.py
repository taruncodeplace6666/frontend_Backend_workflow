import streamlit as st
import pandas as pd
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Contact Manager",
    page_icon="📇",
    layout="wide"
)

# Initialize session state
if "initialized" not in st.session_state:
    st.session_state.initialized = False
if "page" not in st.session_state:
    st.session_state.page = "view"
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

def initialize_database():
    """Initialize database connection and tables"""
    try:
        from db import create_table_if_not_exists, get_all_contacts
        create_table_if_not_exists()
        # Test connection by getting contacts
        get_all_contacts()
        return True, "✅ Database connected successfully!"
    except Exception as e:
        return False, f"❌ Database error: {str(e)}"

def show_database_init():
    """Show database initialization screen"""
    st.title("📊 Contact Manager")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("""
        ## Database Connection Required
        This application requires a PostgreSQL database.
        Click the button below to initialize the connection.
        """)
        
        if st.button("🚀 Initialize Database", type="primary", use_container_width=True):
            with st.spinner("Connecting to database..."):
                success, message = initialize_database()
                if success:
                    st.session_state.initialized = True
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
                    st.info("""
                    **Troubleshooting tips:**
                    1. Make sure PostgreSQL is running
                    2. Check Docker logs: `docker-compose logs db`
                    3. Wait 30 seconds and try again
                    """)

def main_app():
    """Main application after database is initialized"""
    from db import (
        get_all_contacts, create_contact, 
        update_contact, delete_contact, get_contact_by_id,
        search_contacts
    )
    
    # Sidebar
    with st.sidebar:
        st.title("📇 Contact Manager")
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "Navigation",
            ["👁️ View Contacts", "➕ Add Contact", "🔍 Search"],
            key="nav"
        )
        
        if page == "👁️ View Contacts":
            st.session_state.page = "view"
        elif page == "➕ Add Contact":
            st.session_state.page = "add"
        else:
            st.session_state.page = "search"
        
        st.markdown("---")
        
        # Stats
        contacts = get_all_contacts()
        st.metric("Total Contacts", len(contacts))
        
        # Refresh button
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    # Main content
    if st.session_state.page == "view":
        show_view_page(contacts)
    elif st.session_state.page == "add":
        show_add_page()
    elif st.session_state.page == "search":
        show_search_page()

def show_view_page(contacts):
    """Show all contacts"""
    st.title("👁️ View All Contacts")
    
    if not contacts:
        st.info("No contacts found. Add your first contact!")
        return
    
    # Search box
    search_term = st.text_input("🔍 Quick Search", placeholder="Search by name, email, or phone...")
    
    # Filter contacts
    filtered_contacts = contacts
    if search_term:
        filtered_contacts = [
            c for c in contacts
            if search_term.lower() in str(c.get('name', '')).lower() or
               search_term.lower() in str(c.get('email', '')).lower() or
               search_term.lower() in str(c.get('phone', '')).lower()
        ]
    
    if not filtered_contacts:
        st.warning("No contacts match your search.")
        return
    
    # Display as table
    df = pd.DataFrame(filtered_contacts)
    df = df[['id', 'name', 'email', 'phone', 'created_at']]
    df.columns = ['ID', 'Name', 'Email', 'Phone', 'Created']
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID": st.column_config.NumberColumn(width="small"),
            "Name": st.column_config.TextColumn(width="medium"),
            "Email": st.column_config.TextColumn(width="large"),
            "Phone": st.column_config.TextColumn(width="medium"),
            "Created": st.column_config.TextColumn(width="medium")
        }
    )
    
    # Action buttons for each contact
    st.markdown("---")
    st.subheader("Contact Actions")
    
    cols = st.columns(3)
    for idx, contact in enumerate(filtered_contacts[:6]):  # Show first 6
        col = cols[idx % 3]
        with col:
            with st.container(border=True):
                st.markdown(f"**{contact['name']}**")
                st.caption(f"📧 {contact.get('email', 'No email')}")
                st.caption(f"📱 {contact.get('phone', 'No phone')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ Edit", key=f"edit_{contact['id']}", use_container_width=True):
                        st.session_state.edit_id = contact['id']
                        st.session_state.page = "edit"
                        st.rerun()
                with col2:
                    if st.button("🗑️ Delete", key=f"del_{contact['id']}", use_container_width=True):
                        from db import delete_contact
                        if delete_contact(contact['id']):
                            st.success(f"Deleted {contact['name']}")
                            st.rerun()

def show_add_page():
    """Show add contact form"""
    st.title("➕ Add New Contact")
    
    with st.form("add_contact_form", clear_on_submit=True):
        name = st.text_input("Full Name *", placeholder="John Doe")
        email = st.text_input("Email", placeholder="john@example.com")
        phone = st.text_input("Phone", placeholder="+1 (555) 123-4567")
        notes = st.text_area("Notes", placeholder="Additional information...")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button("💾 Save Contact", type="primary", use_container_width=True)
        
        if submitted:
            if not name.strip():
                st.error("Name is required!")
                return
            
            try:
                from db import create_contact
                contact_id = create_contact(name, email if email else None, 
                                           phone if phone else None, 
                                           notes if notes else None)
                st.success(f"✅ Contact saved! ID: {contact_id}")
                st.balloons()
                st.session_state.page = "view"
                st.rerun()
            except Exception as e:
                if "duplicate key" in str(e).lower():
                    st.error("Email already exists! Please use a different email.")
                else:
                    st.error(f"Error saving contact: {str(e)}")

def show_search_page():
    """Show search page"""
    st.title("🔍 Search Contacts")
    
    search_term = st.text_input("Enter search term", 
                               placeholder="Search by name, email, or phone...",
                               key="search_input")
    
    if search_term:
        from db import search_contacts
        results = search_contacts(search_term)
        
        if results:
            st.success(f"Found {len(results)} contact(s)")
            
            for contact in results:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"### {contact['name']}")
                        if contact.get('email'):
                            st.markdown(f"**Email:** {contact['email']}")
                        if contact.get('phone'):
                            st.markdown(f"**Phone:** {contact['phone']}")
                        if contact.get('notes'):
                            st.markdown(f"**Notes:** {contact['notes']}")
                        st.caption(f"Added: {contact.get('created_at', 'N/A')}")
                    
                    with col2:
                        if st.button("View Details", key=f"view_{contact['id']}"):
                            st.session_state.edit_id = contact['id']
                            st.session_state.page = "edit"
                            st.rerun()
        else:
            st.warning("No contacts found matching your search.")
    else:
        st.info("Enter a search term to find contacts.")

# Edit page (triggered from view page)
if st.session_state.get('edit_id') and st.session_state.get('page') == 'edit':
    from db import get_contact_by_id, update_contact
    
    contact = get_contact_by_id(st.session_state.edit_id)
    
    if contact:
        st.title("✏️ Edit Contact")
        
        with st.form("edit_form"):
            name = st.text_input("Name", value=contact['name'])
            email = st.text_input("Email", value=contact.get('email', ''))
            phone = st.text_input("Phone", value=contact.get('phone', ''))
            notes = st.text_area("Notes", value=contact.get('notes', ''))
            
            col1, col2, col3 = st.columns(3)
            with col1:
                save = st.form_submit_button("💾 Save Changes", type="primary")
            with col2:
                cancel = st.form_submit_button("❌ Cancel")
            with col3:
                delete = st.form_submit_button("🗑️ Delete")
            
            if save:
                if update_contact(st.session_state.edit_id, name, email, phone, notes):
                    st.success("✅ Contact updated!")
                    st.session_state.page = "view"
                    st.session_state.edit_id = None
                    st.rerun()
                else:
                    st.error("Failed to update contact")
            
            if cancel:
                st.session_state.page = "view"
                st.session_state.edit_id = None
                st.rerun()
            
            if delete:
                from db import delete_contact
                if delete_contact(st.session_state.edit_id):
                    st.success("✅ Contact deleted!")
                    st.session_state.page = "view"
                    st.session_state.edit_id = None
                    st.rerun()
    else:
        st.error("Contact not found")
        st.session_state.page = "view"
        st.session_state.edit_id = None

# Main app flow
if not st.session_state.initialized:
    show_database_init()
else:
    main_app()

# Footer
st.markdown("---")
st.caption(f"📊 Contact Manager | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
