from pydantic import BaseModel, Field
from typing import Literal

# --- 1. Define Input Schemas (Strict Validation) ---
class TicketPriceInput(BaseModel):
    destination: str = Field(..., description="The city (e.g., 'London', 'LHR')")
    travel_class: Literal['economy', 'business'] = Field('economy', description="Class of travel")

# --- 2. Implement Functions ---
def get_ticket_price(destination: str, travel_class: str = 'economy'):
    # Mock Data
    prices = {
        "london": {"economy": 450, "business": 1200},
        "paris": {"economy": 380, "business": 1100},
        "nyc": {"economy": 200, "business": 600},
        "tokyo": {"economy": 900, "business": 2500}
    }

    city = destination.lower().strip()
    if city in prices:
        price = prices[city].get(travel_class, "N/A")
        return {
            "tool": "get_ticket_price",
            "status": "success", 
            "price": price, 
            "currency": "USD", 
            "destination": city,
            "class": travel_class
        }
    else:
        return {
            "tool": "get_ticket_price",
            "status": "error", 
            "message": f"No pricing found for {destination}"
        }

# --- 3. Registry ---
# The Router will inspect this dictionary to know what tools are available
AVAILABLE_TOOLS = {
    "get_ticket_price": {
        "func": get_ticket_price,
        "schema": TicketPriceInput,
        "description": "Get current flight ticket prices for a specific destination."
    }
}
