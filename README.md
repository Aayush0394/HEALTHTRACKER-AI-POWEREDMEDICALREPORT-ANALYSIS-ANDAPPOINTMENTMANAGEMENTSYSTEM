# Health Appointment Platform + Streamlit RAG Assistant

This repository keeps the **Flask health appointment/report application** and the **RAG document chat in Streamlit** as two separate services. The Flask patient dashboard and admin panel include links to the Streamlit RAG app.

## Project structure

- `health_app/` — Flask application: patient appointments, report analysis, admin and doctor modules.
- `rag_streamlit/` — Streamlit RAG assistant: PDF/TXT upload, chunking, Gemini embeddings, ChromaDB retrieval, grounded answers, and retrieved context.
- `.env.example` — environment variable template.

## Setup (Windows)

1. Install Python 3.10+ and create a `.env` file by copying `.env.example`. Fill in your MongoDB URI, a random Flask secret, and Gemini API key. Never commit `.env`.
2. Terminal 1 — Flask app:
   ```powershell
   cd health_app
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirement.txt
   python app.py
   ```
3. Terminal 2 — Streamlit RAG app:
   ```powershell
   cd rag_streamlit
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   streamlit run app.py --server.port 8501
   ```
4. Open the Flask URL shown in terminal. The patient dashboard and admin panel link to RAG at `http://localhost:8501`.

For deployment, set `RAG_APP_URL` to the deployed Streamlit URL. Deploy the Flask and Streamlit services separately; the RAG app is intentionally **not embedded inside Flask**.

## Important security notes

- MongoDB connection strings and Flask session secrets are read from environment variables. Use your own credentials in `.env`.
- The previous archive contained database credentials in source code. Rotate those credentials in MongoDB Atlas before reuse, even though the copy in this merged project has been replaced.
- The existing admin master-key implementation should be hardened before production deployment.
- Medical AI output is informational and must not replace advice from a qualified clinician.
