# FinAudit AI - Enterprise RAG Engine

FinAudit AI is an advanced, autonomous financial auditing agent designed to parse complex legal loan agreements, calculate precise financial metrics (EMIs, penalties, disbursals), and provide context-aware conversational insights. 

Built with a state-of-the-art Agentic RAG (Retrieval-Augmented Generation) architecture, it leverages Llama 3, LangChain, and Hybrid Search to eliminate AI hallucinations and deliver enterprise-grade accuracy.

![FinAudit AI UI](frontend/public/favicon.ico) **

## 🚀 Key Features

* **Agentic Routing:** Utilizes a high-speed Llama-3.1-8B "Front Door" router to instantly classify and respond to conversational queries, bypassing the heavy RAG pipeline to save tokens and drastically reduce latency.
* **Stateful Conversational Memory:** Integrated with LangChain (`RunnableWithMessageHistory`) to maintain rolling context, allowing users to ask complex, multi-step follow-up questions using natural pronouns (e.g., "Multiply *that* penalty by 12").
* **Hybrid Search Pipeline:** Combines dense vector embeddings (Qdrant), keyword matching (BM25), and Cross-Encoder re-ranking to accurately retrieve complex financial clauses hidden deep within dense legal text.
* **Zero-Hallucination Tool Calling:** Features a secure, Python-based mathematical execution tool accessed via LLM tool-calling, guaranteeing 100% accuracy on financial arithmetic.
* **Dynamic Markdown UI:** A highly responsive React frontend styled with Tailwind CSS v4, featuring a dark/light mode toggle and `@tailwindcss/typography` for beautifully rendered, highly readable AI responses.

## 🛠️ Tech Stack

**Frontend:**
* React (Vite)
* Tailwind CSS v4
* React-Markdown & Tailwind Typography
* Axios & Lucide React (Icons)

**Backend & AI Pipeline:**
* FastAPI (Python)
* Groq Cloud API (Llama-3.3-70B & Llama-3.1-8B)
* LangChain & LangChain-Groq
* Qdrant (Vector Database via Docker)
* Unstructured (Document Parsing)
* Sentence-Transformers (Embeddings & Re-ranking)

---

## ⚙️ Local Setup & Installation

### Prerequisites
* Python 3.9+
* Node.js & npm
* Docker Desktop
* A [Groq API Key](https://console.groq.com/keys)

### 1. Start the Qdrant Vector Database (Docker)
We use Docker to run Qdrant locally and persistently store vector embeddings. Run this command in your main project directory:

**Windows (PowerShell):**
```powershell
docker run -p 6333:6333 -p 6334:6334 -v ${PWD}/qdrant_storage:/qdrant/storage:z qdrant/qdrant


2. Backend Setup
Open a new terminal and navigate to your backend folder (if separated) or root directory.

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn groq langchain langchain-groq langchain-community qdrant-client sentence-transformers python-dotenv pydantic unstructured

# Create a .env file and add your Groq API Key
echo "GROQ_API_KEY=your_actual_api_key_here" > .env

# Start the FastAPI server
uvicorn app:app --reload

3. Frontend Setup
Open a new terminal and navigate to your frontend directory.

cd frontend

# Install dependencies (including markdown parsers)
npm install
npm install react-markdown @tailwindcss/typography

# Start the Vite development server
npm run dev

💡 How to Use
Open the UI at http://localhost:5173.

Click "Upload Agreement" and select a complex .txt, .pdf, or .docx loan agreement.

Test the Agentic Router by saying simply: "Hello!" (Notice the instant response).

Test the RAG Pipeline by asking: "What is my exact EMI amount?"

Test the Stateful Memory & Tools by asking: "What happens if I miss that payment for a month? Now multiply that penalty by 12."


💡 How to Use
Open the UI at http://localhost:5173.

Click "Upload Agreement" and select a complex .txt, .pdf, or .docx loan agreement.

Test the Agentic Router by saying simply: "Hello!" (Notice the instant response).

Test the RAG Pipeline by asking: "What is my exact EMI amount?"

Test the Stateful Memory & Tools by asking: "What happens if I miss that payment for a month? Now multiply that penalty by 12."

🧠 System Architecture
Query Input: User sends a query.

Router (8B Model): Decides if the query is a simple chat (returns instantly) or requires document retrieval.

Query Expansion: Plain English is translated into legal synonyms (e.g., "loan amount" -> "Sanctioned Principal Sum").

Hybrid Retrieval: Qdrant (Vectors) + BM25 (Keywords) retrieve the top matching document chunks.

Re-Ranking: A Cross-Encoder model scores and re-orders the chunks for maximum relevance.

Synthesis (70B Model): LangChain injects past conversation history, reads the retrieved chunks, utilizes the Python calculator tool if math is required, and streams the final Markdown response to the frontend.