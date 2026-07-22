import streamlit as st

from frontend.api_client import get_application, get_me, login, list_applications
from frontend.utils import admin_page, applications_page, dashboard_page, detail_page, process_page

st.set_page_config(
    page_title="Social Support AI",
    page_icon="",
    layout="wide",
)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.page = "Dashboard"
    st.session_state.selected_app_id = None
    st.session_state.process_app_id = None


def _do_login(username: str, password: str) -> bool:
    result = login(username, password)
    if result:
        st.session_state.token = result["access_token"]
        user = get_me()
        if user:
            st.session_state.user = user
            st.session_state.authenticated = True
            return True
    return False


def _logout():
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.user = None
    st.rerun()


if not st.session_state.authenticated:
    st.markdown(
        "<h1 style='text-align: center;'> Social Support AI</h1>"
        "<h3 style='text-align: center;'>AI-Powered Application Workflow Automation</h3>",
        unsafe_allow_html=True,
    )

    with st.container():
        _, col, _ = st.columns([1, 1, 1])
        with col:
            with st.form("login_form"):
                st.subheader("Login")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
                if submitted:
                    if _do_login(username, password):
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
    st.stop()

user = st.session_state.user
role = user.get("role", "") if user else ""

with st.sidebar:
    st.markdown(f"### {user.get('full_name', 'User')}")
    st.markdown(f"**Role:** `{role}`")
    st.divider()

    nav_items = {
        "Dashboard": "dashboard",
        "Applications": "applications",
        "Process": "process",
    }
    if role in ("admin", "reviewer"):
        nav_items["Admin"] = "admin"

    label_to_page = nav_items
    page_to_label = {v: k for k, v in nav_items.items()}
    current_page = st.session_state.get("page", "dashboard")
    current_label = page_to_label.get(current_page, page_to_label.get("applications", list(nav_items.keys())[0]))
    current_index = list(nav_items.keys()).index(current_label)
    selected = st.radio("Navigation", list(nav_items.keys()), index=current_index, key="nav_radio")
    selected_page = nav_items[selected]
    if "nav_last_page" not in st.session_state:
        st.session_state.nav_last_page = selected_page
    if selected_page != st.session_state.nav_last_page:
        st.session_state.nav_last_page = selected_page
        st.session_state.page = selected_page

    st.divider()
    if st.button("Logout", use_container_width=True):
        _logout()

st.sidebar.markdown(
    f"<small>API: {st.session_state.get('api_url', 'connected')}</small>",
    unsafe_allow_html=True,
)

page = st.session_state.get("page", "dashboard")

if page == "dashboard":
    dashboard_page.show()

elif page == "applications":
    applications_page.show()

elif page == "detail":
    app_id = st.session_state.get("selected_app_id")
    if app_id:
        detail_page.show(app_id)
    else:
        st.warning("No application selected")

elif page == "process":
    process_page.show()

elif page == "admin":
    admin_page.show()

else:
    dashboard_page.show()
