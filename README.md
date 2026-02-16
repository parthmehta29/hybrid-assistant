# AI Intelligent Routing System

## Overview
A production-grade AI system that intelligently routes user queries to the most appropriate handler (RAG, Tools, or Small Talk) based on intent. It optimizes for latency and cost by using a hybrid routing approach (Deterministic Regex + Semantic LLM).

## Key Features
- **Hybrid Router:** Extremely fast (<10ms) for common patterns, smart for ambiguous queries.
- **RAG Pipeline:** Includes a "Groundedness Check" to prevent hallucinations.
- **Tool Execution:** Safe, schema-validated function calling using Pydantic.
- **Guardrails:** Input token limits, output validation, and confidence thresholds.
- **Observability:** Structured JSON logging for all requests.

## Architecture
See [Architecture Document](architecture_ai_assignment.md) for full details.

### System Flow
1. **User Query** -> **Guardrails** (Length check)
2. **Router** decides path:
   - *Regex Match* -> **Tools** (e.g., "price of ticket")
   - *Regex Match* -> **Small Talk** (e.g., "hello")
   - *LLM Classifier* -> **RAG** (e.g., "policy for remote work")
   - *LLM Classifier* -> **Out of Scope**
3. **Execution**:
   - Tools: Validated via Pydantic schema.
   - RAG: Retrievals checked for groundedness against the answer.
4. **Response** -> Logged & returned to user.

## Setup & Installation

### Prerequisites
- Python 3.10+
- Google Gemini API Key

### Installation
1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd ai-assignment
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure Environment:
   Create a `.env` file in the root directory:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

### Running the Application
```bash
uvicorn app.main:app --reload
```
Access the API documentation at: `http://127.0.0.1:8000/docs`

## Project Structure
```text
ai-assignment/
├── app/
│   ├── main.py            # FastAPI Entrypoint & Execution Logic
│   ├── router.py          # Hybrid Routing (Regex + Gemini)
│   ├── rag.py             # Vector Store & Groundedness Check
│   ├── tools.py           # Tool Definitions & Schema
│   └── logger.py          # Structured Logging
├── data/
│   ├── knowledge_base.txt # Source data for RAG
│   └── chroma_db/         # Local Vector Store
├── logs/                  # JSON logs
├── requirements.txt
└── README.md
```

## Testing
- **Tools:** Ask "Get ticket price to London".
- **RAG:** Ask "What is the travel policy for international flights?".
- **Refusal:** Ask "How to bake a cake?".

## Authors
- Built for AI Engineering Assessment.
