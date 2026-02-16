from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Any
import json
import time
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Import our components
from app.router import router, RouteType
from app.rag import rag_system
from app.tools import get_ticket_price, TicketPriceInput
from app.logger import logger  # IMPORT NEW LOGGER

load_dotenv()

app = FastAPI(title="AI Intelligent Router")

# --- Models ---
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    route: str
    reason: str
    metadata: dict[str, Any] = {}

# --- Helper: Tool Execution ---
def execute_tool_llm(query: str):
    # Ask Gemini to extract arguments
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    prompt = f"""
    Extract parameters for the function 'get_ticket_price(destination: str, travel_class: str)'.
    Allowed travel_class: 'economy', 'business'.

    Query: "{query}"

    Rule: If travel class is not mentioned, set travel_class to "economy".

    Output JSON ONLY: {{ "destination": "...", "travel_class": "..." }}
    """
    try:
        resp = model.generate_content(prompt)
        text = resp.text.replace("```json", "").replace("```", "").strip()
        args = json.loads(text)

        # Validate with Pydantic
        validated = TicketPriceInput(**args)

        # Call Function
        return get_ticket_price(validated.destination, validated.travel_class)
    except Exception as e:
        return {"error": f"Failed to execute tool: {str(e)}"}

# --- Routes ---

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    # We can't easily log here because we need the route decision, 
    # so we log inside the endpoint instead.
    return response

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    start_time = time.time()
    query = request.query

    # 1. Guardrail: Input Length
    if len(query) > 500:
        logger.log_error("Query too long", {"length": len(query)})
        raise HTTPException(status_code=400, detail="Query too long (max 500 chars).")

    try:
        # 2. Routing Decision
        decision = router.route(query)

        response_text = ""
        metadata = {}

        # 3. Execution Logic
        if decision.route == RouteType.SMALL_TALK:
            response_text = "Hello! I am your corporate assistant. I can help with travel bookings and company policies."

        elif decision.route == RouteType.STRUCTURED_DATA:
            tool_result = execute_tool_llm(query)
            if "error" in tool_result:
                 response_text = f"I encountered an error processing your request: {tool_result['error']}"
                 logger.log_error("Tool execution failed", tool_result)
            else:
                 response_text = f"Here is the pricing info: {json.dumps(tool_result, indent=2)}"
            metadata = tool_result

        elif decision.route == RouteType.RAG:
            rag_result = rag_system.query(query)
            response_text = rag_result["answer"]
            metadata = {
                "grounded": rag_result["grounded"],
                "context_chunks_used": len(rag_result.get("context", [])),
                "original_candidate": rag_result.get("original_candidate", "N/A")
            }

        elif decision.route == RouteType.OUT_OF_SCOPE:
            response_text = "I'm sorry, I cannot answer that. I am limited to company travel policies and booking queries."

        # Log Success
        latency = (time.time() - start_time) * 1000
        logger.log_request(query, decision.route, latency, metadata)

        return ChatResponse(
            answer=response_text,
            route=decision.route,
            reason=decision.reason,
            metadata=metadata
        )

    except Exception as e:
        logger.log_error(f"Unhandled error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/feedback")
async def feedback_endpoint(feedback: dict):
    try:
        with open("data/feedback.json", "a") as f:
            f.write(json.dumps(feedback) + "\n")
        return {"status": "received"}
    except Exception as e:
        logger.log_error(f"Feedback storage error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
