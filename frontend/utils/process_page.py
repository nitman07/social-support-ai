import time

import streamlit as st

from frontend.api_client import get_application, get_status, list_applications, process_application


def show():
    st.title("Process Application")

    apps = list_applications(page_size=50)
    items = apps.get("items", [])

    draft_items = [a for a in items if a["status"] in ("draft", "failed")]
    if not draft_items:
        st.info("No applications available for processing")
        return

    app_options = {f"{a['applicant_name']} ({a['id'][:8]})": a["id"] for a in draft_items}
    selected_label = st.selectbox("Select Application", list(app_options.keys()))

    if selected_label:
        app_id = app_options[selected_label]
        app = get_application(app_id)
        if app:
            st.markdown(f"**Status:** `{app['status']}`")

            if st.button("🚀 Start Workflow", type="primary", use_container_width=True):
                with st.spinner("Triggering workflow..."):
                    result = process_application(app_id)
                if result:
                    st.success(f"Workflow started: `{result['workflow_id']}`")
                    placeholder = st.empty()
                    for _ in range(60):
                        time.sleep(2)
                        status = get_status(app_id)
                        if status:
                            s = status["status"]
                            placeholder.info(f"Status: **{s}**")
                            if s in ("approved", "declined", "completed", "failed"):
                                if status.get("decision"):
                                    st.success(f"Decision: **{status['decision']}** | ML Score: {status.get('ml_score', 'N/A')}")
                                break
                else:
                    st.error("Failed to trigger workflow")
