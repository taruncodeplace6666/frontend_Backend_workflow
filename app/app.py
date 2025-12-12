
import streamlit as st
from db import (
    create_table_if_not_exists,
    create_contact,
    get_all_contacts,
    get_contact_by_id,
    update_contact,
    delete_contact,
)

st.set_page_config(page_title="Contacts CRUD", layout="centered")
create_table_if_not_exists()

st.title("Contacts — Streamlit + PostgreSQL (CRUD)")

menu = st.sidebar.selectbox("Choose action", ["Create", "Read", "Update", "Delete", "Search"])

if menu == "Create":
    st.header("Create a new contact")
    with st.form("create_form"):
        name = st.text_input("Name", max_chars=100)
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Create")
    if submitted:
        if not name.strip():
            st.error("Name is required.")
        else:
            try:
                new_id = create_contact(name.strip(), email.strip() or None, phone.strip() or None, notes.strip() or None)
                st.success(f"Contact created with id: {new_id}")
            except Exception as e:
                st.error(f"Error creating contact: {e}")

elif menu == "Read":
    st.header("All contacts")
    rows = get_all_contacts()
    if not rows:
        st.info("No contacts yet.")
    else:
        # Display as a table
        st.dataframe(rows)
        # Show details on selection
        sel = st.selectbox("Select contact to view details", options=[f"{r['id']}: {r['name']}" for r in rows])
        if sel:
            cid = int(sel.split(":")[0])
            item = get_contact_by_id(cid)
            st.write(item)

elif menu == "Update":
    st.header("Update a contact")
    rows = get_all_contacts()
    if not rows:
        st.info("No contacts to update.")
    else:
        sel = st.selectbox("Choose contact to update", options=[f"{r['id']}: {r['name']}" for r in rows])
        cid = int(sel.split(":")[0])
        contact = get_contact_by_id(cid)
        with st.form("update_form"):
            name = st.text_input("Name", value=contact["name"])
            email = st.text_input("Email", value=contact["email"] or "")
            phone = st.text_input("Phone", value=contact["phone"] or "")
            notes = st.text_area("Notes", value=contact["notes"] or "")
            updated = st.form_submit_button("Update")
        if updated:
            try:
                count = update_contact(cid, name.strip(), email.strip() or None, phone.strip() or None, notes.strip() or None)
                if count:
                    st.success("Contact updated.")
                else:
                    st.warning("No rows updated (maybe no change).")
            except Exception as e:
                st.error(f"Error updating contact: {e}")

elif menu == "Delete":
    st.header("Delete a contact")
    rows = get_all_contacts()
    if not rows:
        st.info("No contacts to delete.")
    else:
        sel = st.selectbox("Choose contact to delete", options=[f"{r['id']}: {r['name']}" for r in rows])
        cid = int(sel.split(":")[0])
        if st.button("Delete"):
            try:
                count = delete_contact(cid)
                if count:
                    st.success("Contact deleted.")
                else:
                    st.warning("No contact deleted.")
            except Exception as e:
                st.error(f"Error deleting contact: {e}")

elif menu == "Search":
    st.header("Search contacts by name or email (simple)")
    q = st.text_input("Search term (name or email)")
    if q:
        rows = get_all_contacts()
        filtered = [r for r in rows if q.lower() in (r["name"] or "").lower() or q.lower() in (r["email"] or "").lower()]
        st.write(f"Found {len(filtered)} result(s).")
        st.dataframe(filtered)

