# FinAudit AI - Enterprise RAG Engine

FinAudit AI is an advanced, autonomous financial auditing agent designed to parse complex legal loan agreements, calculate precise financial metrics (EMIs, penalties, disbursals), and provide context-aware conversational insights. 

Built with a state-of-the-art Agentic RAG (Retrieval-Augmented Generation) architecture, it leverages Llama 3, LangChain, and Hybrid Search to eliminate AI hallucinations and deliver enterprise-grade accuracy.

![FinAudit AI UI](frontend/public/favicon.ico) 

## 🚀 Key Enterprise Features

* **Multi-Tenant Data Isolation:** Secure JWT-based authentication ensures that each user's uploaded documents and chats are strictly isolated at the database layer.
* **Agentic Routing:** Utilizes a high-speed Llama-3.1-8B "Front Door" router to instantly classify and respond to conversational queries, bypassing the heavy RAG pipeline to save tokens.
* **Hybrid Search Pipeline:** Combines dense vector embeddings (Qdrant), keyword matching (BM25), and Cross-Encoder re-ranking to accurately retrieve complex financial clauses.
* **LLM-as-a-Judge Evaluation:** Includes an automated testing pipeline (`run_evals.py`) where a 70B model grades the RAG system's output for Faithfulness and Relevance.
* **Modular Microservices Architecture:** A scalable FastAPI backend divided into clean, maintainable routing modules.

## 🛠️ Tech Stack

**Frontend:**
* React (Vite)
* Tailwind CSS v4 (Zinc Minimalist Theme)
* React-Markdown & Tailwind Typography
* Axios & Lucide React (Icons)

**Backend & AI Pipeline:**
* FastAPI (Python)
* PostgreSQL (asyncpg) & SQLAlchemy (Relational Data & Users)
* Qdrant (Vector Database via Docker)
* Groq Cloud API (Llama-3.3-70B & Llama-3.1-8B)
* LangChain & LangChain-Groq
* Sentence-Transformers & rank-bm25 (Embeddings & Re-ranking)

---

## ⚙️ Local Setup & Installation

### Prerequisites
* Python 3.9+
* Node.js & npm
* Docker Desktop
* PostgreSQL Server running locally

### 1. Start the Databases
Make sure PostgreSQL is running. Then, start the Qdrant Vector Database via Docker in your main project directory:

```powershell
docker run -p 6333:6333 -p 6334:6334 -v ${PWD}/qdrant_storage:/qdrant/storage:z qdrant/qdrant