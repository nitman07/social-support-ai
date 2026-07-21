import streamlit as st

from frontend.api_client import list_applications


def show():
    st.title("Applications")

    col_filter, col_paginate = st.columns([3, 1])
    with col_filter:
        status_filter = st.selectbox(
            "Filter by status",
            options=["All", "draft", "processing", "approved", "declined", "failed", "awaiting_review"],
            index=0,
        )

    with col_paginate:
        page = st.number_input("Page", min_value=1, value=1, step=1)

    status = None if status_filter == "All" else status_filter
    result = list_applications(status=status, page=page, page_size=15)
    items = result.get("items", [])
    total = result.get("total", 0)

    st.markdown(f"Showing {len(items)} of {total} applications")

    if not items:
        st.info("No applications match the current filter")
        return

    for app in items:
        with st.container(border=True):
            ca = app.get("created_at", "")[:19] if app.get("created_at") else ""
            sa = app.get("submitted_at", "")[:19] if app.get("submitted_at") else ""
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            col1.write(f"**{app['applicant_name']}**")
            col2.write(f"`{app['status']}`")
            col3.write(ca)
            if col4.button("Detail", key=f"detail_{app['id']}"):
                st.session_state["selected_app_id"] = app["id"]
                st.session_state["page"] = "detail"
                st.rerun()
            if col5.button("Process", key=f"process_{app['id']}"):
                st.session_state["process_app_id"] = app["id"]
                st.session_state["page"] = "process"
                st.rerun()
