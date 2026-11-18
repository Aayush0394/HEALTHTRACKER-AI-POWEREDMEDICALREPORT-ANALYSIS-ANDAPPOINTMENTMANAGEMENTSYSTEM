@echo off
start "Health Flask App" cmd /k "cd /d %~dp0health_app && python app.py"
start "RAG Streamlit App" cmd /k "cd /d %~dp0rag_streamlit && streamlit run app.py --server.port 8501"
