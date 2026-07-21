import streamlit as st

from frontend.api_client import get_application, get_flags, resolve_flag, signoff


def show(app_id: str):
    app = get_application(app_id)
    if not app:
        st.error("Application not found")
        return

    st.title(f"Application: {app['applicant']['full_name']}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Status:** `{app['status']}`")
        st.markdown(f"**Workflow ID:** `{app.get('workflow_id', 'N/A')}`")
    with col2:
        st.markdown(f"**Nationality:** {app['applicant']['nationality']}")
        st.markdown(f"**Emirates ID:** {app['applicant']['emirates_id']}")

    st.divider()

    assessment = app.get("assessment")
    if assessment:
        st.subheader("Assessment")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("ML Score", f"{assessment.get('ml_score', 'N/A')}")
        col_b.metric("Confidence", f"{assessment.get('ml_confidence', 'N/A')}")
        col_c.metric("Decision", assessment.get("decision", "N/A"))
        if assessment.get("llm_rationale"):
            with st.expander("LLM Rationale"):
                st.write(assessment["llm_rationale"])

    st.divider()
    st.subheader("Documents")
    for doc in app.get("documents", []):
        col_d1, col_d2, col_d3 = st.columns([3, 1, 1])
        col_d1.write(f"**{doc['document_type']}** — {doc['file_name']}")
        col_d2.write(f"OCR: {doc['ocr_status']}")
        col_d3.write(f"Conf: {doc.get('ocr_confidence', 'N/A')}")

    st.divider()
    st.subheader("Inconsistencies")
    flags = get_flags(app_id)
    if flags:
        for flag in flags:
            with st.container(border=True):
                col_f1, col_f2 = st.columns([3, 1])
                col_f1.write(f"**{flag['field']}** ({flag['severity']})")
                col_f1.write(f"{flag['source_a']}: {flag['value_a']} vs {flag['source_b']}: {flag['value_b']}")
                if flag["status"] == "open":
                    if col_f2.button("Accept", key=f"accept_{flag['id']}"):
                        resolve_flag(app_id, flag["id"], "accept")
                        st.rerun()
                    if col_f2.button("Reject", key=f"reject_{flag['id']}"):
                        resolve_flag(app_id, flag["id"], "reject")
                        st.rerun()
                else:
                    col_f2.write(f"Status: {flag['status']}")
    else:
        st.info("No inconsistencies found")

    st.divider()
    st.subheader("Recommendations")
    for rec in app.get("recommendations", []):
        with st.container(border=True):
            st.markdown(f"**{rec['title']}** ({rec['category']})")
            if rec.get("description"):
                st.write(rec["description"])
            if rec.get("relevance_score"):
                st.metric("Relevance", f"{rec['relevance_score']:.2%}")

    if app["status"] in ("approved", "declined", "completed"):
        st.divider()
        st.subheader("Human-in-the-Loop Signoff")
        if app["status"] in ("approved", "declined"):
            st.info(f"Final decision: **{app['status']}**")
        else:
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                if st.button("Approve", type="primary", use_container_width=True):
                    if signoff(app_id, "approved", "Approved by reviewer"):
                        st.success("Application approved")
                        st.rerun()
            with col_s2:
                if st.button("Decline", type="secondary", use_container_width=True):
                    if signoff(app_id, "declined", "Declined by reviewer"):
                        st.success("Application declined")
                        st.rerun()
