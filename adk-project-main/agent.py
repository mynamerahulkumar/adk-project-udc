import os
import sys
import requests
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Handle both direct script execution and module import
try:
    from .datastore import search_documents
    from .search_agent import search_with_grounding
except ImportError:
    from datastore import search_documents
    from search_agent import search_with_grounding

# Load environment variables
load_dotenv()

# Configure short-term session to use the in-memory service
session_service = InMemorySessionService()

# Read the instructions from a file in the same
# directory as this agent.py file.
script_dir = os.path.dirname(os.path.abspath(__file__))
instruction_file_path = os.path.join(script_dir, "agent-prompt.txt")
with open(instruction_file_path, "r") as f:
    instruction = f.read()

# Define the get-product-price tool as a Python function
def get_product_price(product_name: str) -> str:
    """
    Get the price of a product from the bird store inventory.
    
    Args:
        product_name: The name of the product to look up (e.g., "Bird Seed Mix")
    
    Returns:
        A formatted string with the product name and price
    """
    toolbox_url = os.getenv("TOOLBOX_URL", "http://localhost:8000")
    try:
        response = requests.post(
            f"{toolbox_url}/tools/get-product-price/call",
            json={"product_name": product_name},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return f"Product: {data['product_name']}, Price: ${data['price']:.2f}"
        elif response.status_code == 404:
            error_data = response.json()
            return f"Product not found: {error_data.get('error', 'Unknown error')}"
        else:
            return f"Error querying database: {response.text}"
    except requests.exceptions.RequestException as e:
        return f"Error connecting to toolbox: {str(e)}"

# Set up the tools that we will be using for the root agent
# Part 1: Session management and guardrails (core)
# Part 2: Database tool (get-product-price)
# Part 3: Document search tool (search_documents)
# Part 4: Grounding with Google Search tool (search_with_grounding)
tools = [get_product_price, search_documents, search_with_grounding]

# Create our agent
root_agent = Agent(
    model="gemini-2.5-flash",
    name="root_agent",
    instruction=instruction,
    tools=tools
)

# Create runner for the agent
runner = Runner(
    agent=root_agent,
    app_name="bird_store_agent",
    session_service=session_service
)