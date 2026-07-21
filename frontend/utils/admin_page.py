import streamlit as st

from frontend.api_client import get_flags, list_applications, resolve_flag, resume_workflow, signoff


def show():
    st.title("Admin Panel")

    tab1, tab2 = st.tabs(["Flag Queue", "Awaiting Review"])

    with tab1:
        st.subheader("Open Flags")
        apps = list_applications(page_size=100)
        all_flags = []
        for app in apps.get("items", []):
            flags = get_flags(app["id"])
            for f in flags:
                if f["status"] == "open":
                    all_flags.append({**f, "applicant_name": app["applicant_name"], "app_id": app["id"]})

        if not all_flags:
            st.info("No open flags")
        else:
            for f in all_flags:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    col1.markdown(f"**{f['field']}** — {f['applicant_name']} ({f['severity']})")
                    col1.write(f"{f['source_a']}: {f['value_a']} vs {f['source_b']}: {f['value_b']}")
                    if col2.button("Accept", key=f"adm_acc_{f['id']}"):
                        resolve_flag(f["app_id"], f["id"], "accept")
                        st.rerun()
                    if col2.button("Reject", key=f"adm_rej_{f['id']}"):
                        resolve_flag(f["app_id"], f["id"], "reject")
                        st.rerun()

    with tab2:
        st.subheader("Awaiting Human Review")
        review_apps = list_applications(status="awaiting_review", page_size=50)
        items = review_apps.get("items", [])
        if not items:
            st.info("No applications awaiting review")
        else:
            for app in items:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    col1.write(f"**{app['applicant_name']}**")
                    if col2.button("Approve", key=f"appr_{app['id']}"):
                        signoff(app["id"], "approved", "Admin approved")
                        st.rerun()
                    if col3.button("Decline", key=f"decl_{app['id']}"):
                        signoff(app["id"], "declined", "Admin declined")
                        st.rerun()
                    st.write(f"Workflow: {app.get('workflow_id', 'N/A')}")
                    if st.button("Resume Workflow", key=f"resume_{app['id']}"):
                        resume_workflow(app["id"])
                        st.rerun()
