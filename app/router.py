from enum import Enum
from pydantic import BaseModel, Field
import re
import json
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# Using 'models/gemini-1.5-flash' as requested
model = genai.GenerativeModel('models/gemini-2.5-flash')


class RouteType(str, Enum):
    SMALL_TALK = "small_talk"
    STRUCTURED_DATA = "structured_data"
    RAG = "rag"
    OUT_OF_SCOPE = "out_of_scope"

class RouteDecision(BaseModel):
    route: RouteType
    reason: str
    confidence: float

class HybridRouter:
    def __init__(self):
        # 1. Deterministic Rules (Fast Lane)
        self.rules = {
            RouteType.SMALL_TALK: [
                r"\b(hi|hello|hey|greetings)\b",
                r"\b(who are you|your name)\b"
            ],
            RouteType.STRUCTURED_DATA: [
                r"\b(ticket|flight|price|cost|book)\b.*\b(to|from)\b",
                r"\b(how much)\b.*\b(flight|ticket)\b"
            ]
        }

    def _check_rules(self, query: str) -> RouteDecision | None:
        query_lower = query.lower()

        # Check Small Talk
        for pattern in self.rules[RouteType.SMALL_TALK]:
            if re.search(pattern, query_lower):
                return RouteDecision(
                    route=RouteType.SMALL_TALK,
                    reason=f"Matched greeting pattern: '{pattern}'",
                    confidence=1.0
                )

        # Check Structured Data (Tools)
        for pattern in self.rules[RouteType.STRUCTURED_DATA]:
            if re.search(pattern, query_lower):
                return RouteDecision(
                    route=RouteType.STRUCTURED_DATA,
                    reason=f"Matched tool pattern: '{pattern}'",
                    confidence=1.0
                )

        return None

    def _semantic_route(self, query: str) -> RouteDecision:
        # 2. Semantic Routing (Slow Lane)
        prompt = f"""
        Act as a query router. Classify the user query into ONE of these categories:

        1. RAG: The user is asking for factual information about company policies (travel, expense, remote work).
        2. OUT_OF_SCOPE: The user is asking about coding, math, general world knowledge, or dangerous topics.
        3. SMALL_TALK: Greetings or simple conversational inputs.

        Query: "{query}"

        Output JSON only:
        {{
            "route": "rag" | "out_of_scope" | "small_talk",
            "reason": "brief explanation",
            "confidence": 0.9
        }}
        """

        try:
            response = model.generate_content(prompt)
            text = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(text)

            return RouteDecision(
                route=RouteType(data['route'].lower()),
                reason=data.get('reason', 'LLM classification'),
                confidence=float(data.get('confidence', 0.5))
            )
        except Exception as e:
            return RouteDecision(
                route=RouteType.OUT_OF_SCOPE,
                reason=f"Routing failed: {str(e)}",
                confidence=0.0
            )

    def route(self, query: str) -> RouteDecision:
        decision = self._check_rules(query)
        if decision:
            return decision
        return self._semantic_route(query)

router = HybridRouter()
