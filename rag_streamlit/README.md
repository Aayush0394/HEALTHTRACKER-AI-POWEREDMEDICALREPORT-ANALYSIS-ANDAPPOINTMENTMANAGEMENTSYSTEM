# 📄 Document RAG Assistant (Google Gemini)

**Industrial Training Project**  
**Swami Keshvanand Institute of Technology, Management & Gramothan (SKIT), Jaipur**

| Field            | Details                          |
|------------------|----------------------------------|
| **Submitted By** | Kripendra Singh                  |
| **Roll No.**     | 23ESKCY023                       |
| **Submitted To** | Shivank Lavania                  |
| **Training**     | R-CAT – Microsoft Certified: Azure AI Engineer Associate |

---

## 🎯 Project Overview

AI-powered conversational app that lets users upload **PDF / TXT** documents and ask questions in natural language. Answers are **grounded** in the document using Retrieval-Augmented Generation (RAG) with **Google Gemini**.

---

## 🛠️ Technology Stack

| Component         | Technology                          |
|-------------------|-------------------------------------|
| Frontend          | Streamlit                           |
| LLM               | **Google Gemini 2.0 Flash**         |
| Embeddings        | **Google text-embedding-004**       |
| Vector Database   | ChromaDB (in-memory)                |
| Document Loading  | LangChain PyPDFLoader / TextLoader |
| Text Splitting    | RecursiveCharacterTextSplitter      |
| Language          | Python 3.10+                        |

---

## ✨ Features

- Upload PDF or TXT
- Adjustable chunk size, overlap & Top-K
- Semantic search with Gemini embeddings + ChromaDB
- Grounded answers (no hallucination outside the document)
- Source & page citations
- Chat history

---

## 🔑 Get Free Gemini API Key

1. Open → [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Sign in with Google account
3. Click **Create API key**
4. Copy the key (starts with `AIza...`)

---

## 🚀 Setup & Run

```bash
cd document-rag-assistant

# 1. Virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 2. Install packages
pip install -r requirements.txt

# 3. (Optional) Save key in .env
cp .env.example .env
# Edit .env → GOOGLE_API_KEY=AIza...

# 4. Run
streamlit run app.py
```

App opens at **http://localhost:8501**

### Using the app
1. Paste Gemini API key in the **sidebar**
2. Upload a PDF or TXT (try `sample_document.txt`)
3. Click **🚀 Process Document**
4. Ask questions in the chat box

---

## 🏗️ Architecture

```
Upload PDF/TXT → Load → Chunk → Gemini Embeddings → ChromaDB
                                                      ↓
User Question → Similarity Search (Top-K) → Gemini 2.0 Flash → Answer
```

---

## 🔮 Future Scope

- Multi-document (DOCX, CSV, MD)
- Cloud vector DBs (Pinecone / Qdrant)
- Hybrid search + re-ranking
- Local models via Ollama

---

## 📁 Project Structure

```
document-rag-assistant/
├── app.py
├── requirements.txt
├── .env.example
├── sample_document.txt
└── README.md
```

---

**Thank You**  
SKIT Jaipur · Kripendra Singh · 23ESKCY023
