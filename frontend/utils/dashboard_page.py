import streamlit as st

from frontend.api_client import get_me, list_applications


def show():
    st.title("Dashboard")

    user = get_me()
    if user:
        st.markdown(f"Welcome, **{user.get('full_name', user['username'])}** ({user['role']})")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        result = list_applications(page_size=1)
        total = result.get("total", 0)
        st.metric("Total Applications", total)

    with col2:
        pending = list_applications(status="draft", page_size=1)
        pending_total = pending.get("total", 0)
        st.metric("Draft", pending_total)

    with col3:
        approved = list_applications(status="approved", page_size=1)
        st.metric("Approved", approved.get("total", 0))

    with col4:
        declined = list_applications(status="declined", page_size=1)
        st.metric("Declined", declined.get("total", 0))

    st.divider()
    st.subheader("Recent Applications")
    recent = list_applications(page=1, page_size=5)
    items = recent.get("items", [])
    if items:
        for app in items:
            with st.container(border=True):
                ca = app.get("created_at", "")[:19] if app.get("created_at") else ""
                col_a, col_b, col_c = st.columns([3, 1, 1])
                col_a.write(f"**{app['applicant_name']}** — {app['status']}")
                col_b.write(ca)
                if col_c.button("View", key=f"view_{app['id']}"):
                    st.session_state["selected_app_id"] = app["id"]
                    st.session_state["detail_prev_page"] = "dashboard"
                    st.session_state["page"] = "detail"
                    st.rerun()
    else:
        st.info("No applications found")
