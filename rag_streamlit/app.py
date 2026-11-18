"""
Document RAG Assistant (Google Gemini version)
Industrial Training Project - Swami Keshvanand Institute of Technology (SKIT), Jaipur
Submitted by: Kripendra Singh (23ESKCY023)
"""

import os
import tempfile
from typing import List, Optional

import streamlit as st
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# ---------------------------------------------------------------------------
# Page config & styling
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Document RAG Assistant",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #5A6A7A;
        margin-bottom: 1.5rem;
    }
    .stChatMessage {
        border-radius: 12px;
    }
    div[data-testid="stSidebar"] {
        background-color: #F7F9FC;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def get_google_api_key() -> Optional[str]:
    """Resolve Google / Gemini API key from sidebar input or environment."""
    key = st.session_state.get("google_api_key") or os.getenv("GOOGLE_API_KEY")
    return key.strip() if key else None


def load_document(uploaded_file) -> List[Document]:
    """Load PDF or TXT file into LangChain Documents using a temp file."""
    suffix = os.path.splitext(uploaded_file.name)[1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name

    try:
        if suffix == ".pdf":
            loader = PyPDFLoader(tmp_path)
        elif suffix == ".txt":
            loader = TextLoader(tmp_path, encoding="utf-8")
        else:
            raise ValueError(f"Unsupported file type: {suffix}")
        docs = loader.load()
        for d in docs:
            d.metadata["source"] = uploaded_file.name
        return docs
    finally:
        os.unlink(tmp_path)


def split_documents(
    documents: List[Document], chunk_size: int, chunk_overlap: int
) -> List[Document]:
    """Split documents with RecursiveCharacterTextSplitter."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(documents)


def create_vectorstore(chunks: List[Document], api_key: str) -> Chroma:
    """Embed chunks with Gemini embeddings and store in in-memory Chroma."""
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=api_key,
    )
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name="document_rag",
    )
    return vectorstore


def format_docs(docs: List[Document]) -> str:
    """Join retrieved document chunks into a single context string."""
    return "\n\n---\n\n".join(
        f"[Source: {d.metadata.get('source', 'unknown')} | Page: {d.metadata.get('page', 'N/A')}]\n{d.page_content}"
        for d in docs
    )


def build_rag_chain(vectorstore: Chroma, api_key: str, top_k: int):
    """Build a retrieval + generation chain with strict grounded instructions."""
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": top_k},
    )

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        google_api_key=api_key,
    )

    system_prompt = """You are a helpful Document RAG Assistant.
Answer the user's question STRICTLY based on the provided context from the uploaded document(s).
If the answer cannot be found in the context, clearly say:
"I could not find relevant information in the uploaded document(s) to answer this question."
Do not invent facts. Do not use external knowledge.
When possible, mention the source file and page number.

Context:
{context}
"""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{question}"),
        ]
    )

    chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain, retriever


# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "processed_file" not in st.session_state:
    st.session_state.processed_file = None
if "chunk_count" not in st.session_state:
    st.session_state.chunk_count = 0


# ---------------------------------------------------------------------------
# Sidebar – controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.image(
        "https://www.skit.ac.in/images/headers/skit_logo.png",
        width=180,
    )
    st.markdown("### ⚙️ Configuration")

    api_key_input = st.text_input(
        "Google Gemini API Key",
        type="password",
        placeholder="AIza...",
        help="Get free key from https://aistudio.google.com/apikey",
        key="api_key_widget",
    )
    if api_key_input:
        st.session_state.google_api_key = api_key_input

    st.divider()

    st.markdown("### 📄 Document Upload")
    uploaded_file = st.file_uploader(
        "Upload PDF or TXT",
        type=["pdf", "txt"],
        help="Single document supported. Re-upload to replace.",
    )

    st.markdown("### 🔧 Processing Parameters")
    chunk_size = st.slider(
        "Chunk Size",
        min_value=200,
        max_value=2000,
        value=800,
        step=100,
        help="Size of each text chunk for embedding.",
    )
    chunk_overlap = st.slider(
        "Chunk Overlap",
        min_value=0,
        max_value=400,
        value=150,
        step=50,
        help="Overlap between consecutive chunks.",
    )
    top_k = st.slider(
        "Top-K Retrieval",
        min_value=1,
        max_value=10,
        value=4,
        help="Number of most relevant chunks to retrieve.",
    )

    process_btn = st.button(
        "🚀 Process Document",
        type="primary",
        use_container_width=True,
        disabled=uploaded_file is None,
    )

    if st.session_state.processed_file:
        st.success(f"✅ Ready: **{st.session_state.processed_file}**")
        st.caption(f"Chunks indexed: {st.session_state.chunk_count}")

    st.divider()
    st.caption("Document RAG Assistant · SKIT Jaipur")
    st.caption("Kripendra Singh · 23ESKCY023")
    st.caption("Powered by Google Gemini")


# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.markdown('<p class="main-header">📄 Document RAG Assistant</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">Upload a document → Ask questions → Get grounded answers powered by Gemini RAG</p>',
    unsafe_allow_html=True,
)

# Process document
if process_btn and uploaded_file is not None:
    api_key = get_google_api_key()
    if not api_key:
        st.error("Please provide a valid Google Gemini API Key in the sidebar.")
    else:
        with st.spinner("Loading, chunking & embedding document… this may take a moment"):
            try:
                raw_docs = load_document(uploaded_file)
                chunks = split_documents(raw_docs, chunk_size, chunk_overlap)
                vectorstore = create_vectorstore(chunks, api_key)

                st.session_state.vectorstore = vectorstore
                st.session_state.processed_file = uploaded_file.name
                st.session_state.chunk_count = len(chunks)
                st.session_state.messages = []  # reset chat on new document

                st.success(
                    f"Successfully processed **{uploaded_file.name}** "
                    f"into **{len(chunks)}** chunks."
                )
            except Exception as e:
                st.error(f"Error while processing document: {e}")
                st.session_state.vectorstore = None


# Chat interface
if st.session_state.vectorstore is None:
    st.info(
        "👈 Upload a PDF or TXT file in the sidebar, adjust parameters if needed, "
        "then click **Process Document** to start chatting."
    )
    st.markdown(
        """
        **How to get a free Gemini API key:**
        1. Go to [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
        2. Sign in with your Google account
        3. Click **Create API key**
        4. Copy the key and paste it in the sidebar
        """
    )
else:
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if question := st.chat_input("Ask a question about your document…"):
        api_key = get_google_api_key()
        if not api_key:
            st.error("Google Gemini API Key is missing.")
        else:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                with st.spinner("Retrieving context & generating answer…"):
                    try:
                        chain, retriever = build_rag_chain(
                            st.session_state.vectorstore, api_key, top_k
                        )
                        answer = chain.invoke(question)

                        retrieved = retriever.invoke(question)
                        st.markdown(answer)

                        with st.expander("📚 Retrieved context (Top-K chunks)"):
                            for i, doc in enumerate(retrieved, 1):
                                src = doc.metadata.get("source", "unknown")
                                page = doc.metadata.get("page", "N/A")
                                st.markdown(
                                    f"**Chunk {i}** — `{src}` (page {page})\n\n"
                                    f"{doc.page_content[:500]}{'…' if len(doc.page_content) > 500 else ''}"
                                )

                        st.session_state.messages.append(
                            {"role": "assistant", "content": answer}
                        )
                    except Exception as e:
                        error_msg = f"Error generating answer: {e}"
                        st.error(error_msg)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": error_msg}
                        )
