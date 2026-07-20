import streamlit as st

st.set_page_config(
    page_title="Social Support AI",
    page_icon="🤝",
    layout="wide",
)

st.title("Social Support AI")
st.markdown("### AI-Powered Social Support Application Workflow Automation")

st.info(
    "This application is under construction. "
    "The frontend will be available in a future milestone."
)

st.markdown("""
## Available APIs

- **API Documentation:** [http://localhost:8001/docs](http://localhost:8001/docs)
- **Health Check:** [http://localhost:8001/health](http://localhost:8001/health)
- **PostgreSQL:** `localhost:5433`
- **MongoDB:** `localhost:27017`
- **Qdrant:** `localhost:6335`
- **Neo4j:** `localhost:7474` (browser) / `localhost:7687` (bolt)
- **Ollama:** `localhost:11434`
""")
