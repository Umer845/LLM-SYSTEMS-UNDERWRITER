import streamlit as st
from pathlib import Path
import app
import dashboard
import qa
from utils.db_utils import create_user, validate_user

# ✅ Custom CSS (optional)
st.markdown("""<style>
/* Add your custom CSS here */
</style>""", unsafe_allow_html=True)

# ✅ ---- SESSION ----
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'active_page' not in st.session_state:
    st.session_state['active_page'] = "Login"

# ✅ ---- AUTH ----
if not st.session_state['logged_in']:

    if st.session_state['active_page'] == "Login":
        st.subheader("🔐 Login")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login Now"):
            user = validate_user(username, password)
            if user:
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['user_id'] = user[0]
                st.session_state['active_page'] = "Dashboard"
                st.success("✅ Login successful.")
                st.rerun()
            else:
                st.error("❌ Invalid credentials.")

        if st.button("Go to Register"):
            st.session_state['active_page'] = "Register"
            st.rerun()

    elif st.session_state['active_page'] == "Register":
        st.subheader("📝 Register")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        cnic = st.text_input("CNIC")
        make_name = st.text_input("Make Name")

        if st.button("Register Now"):
            try:
                create_user(username, password, cnic, make_name)
                st.success("✅ Registration successful! Please login.")
                st.session_state['active_page'] = "Login"
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

        if st.button("Back to Login"):
            st.session_state['active_page'] = "Login"
            st.rerun()

else:
    # ✅ ---- SIDEBAR ----
    with st.sidebar:
        st.title(f"👋 Hello, {st.session_state['username']}")
        page = st.radio("Navigate", ["Dashboard", "Upload File", "Risk Profile", "Premium Calculation", "Question Answer", "Logout"])
        st.session_state['active_page'] = page

    # ✅ ---- PAGES ----
    if st.session_state['active_page'] == "Dashboard":
        dashboard.show_dashboard()
    elif st.session_state['active_page'] == "Upload File":
        app.run_app()
    elif st.session_state['active_page'] == "Risk Profile":
        app.run_app()
    elif st.session_state['active_page'] == "Premium Calculation":
        app.run_app()
    elif st.session_state['active_page'] == "Question Answer":
        qa.show_question_answer()
    elif st.session_state['active_page'] == "Logout":
        st.session_state.clear()
        st.success("✅ You have been logged out.")
        st.rerun()
