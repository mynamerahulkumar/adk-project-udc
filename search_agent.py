import os
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Read the instructions from a file in the same
# directory as this file.
script_dir = os.path.dirname(os.path.abspath(__file__))
instruction_file_path = os.path.join(script_dir, "search-prompt.txt")
with open(instruction_file_path, "r") as f:
    instruction = f.read()

# Create search agent with Google Search grounding
# This agent uses Grounding with Google Search to find information
# on the web for questions not covered in local documents
# Note: Uses gemini-2.5-flash model with google_search tool for grounding
# This is a SEPARATE model configuration from the root agent
_search_agent_instance = Agent(
    name="search_agent",
    model="gemini-2.5-flash",
    instruction=instruction,
    description="Answers general knowledge questions using Google Search grounding",
    tools=[google_search]  # Enable Google Search grounding - this tool enables grounding mode
)

# Create session service for the search agent
_search_agent_session = InMemorySessionService()

# Create runner for the search agent
_search_agent_runner = Runner(
    agent=_search_agent_instance,
    app_name="search_agent_tool",
    session_service=_search_agent_session
)

# Create a wrapper function that can be used as a tool by the root agent
def search_with_grounding(query: str) -> str:
    """
    Search for general knowledge information using Google Search grounding.
    
    This tool searches the web for information on topics not covered in local documents,
    providing answers grounded in real-time web search results with citations.
    
    Args:
        query: The search query or question to find information about
    
    Returns:
        A formatted string with search results and source citations
    """
    try:
        import asyncio
        
        # Create and run async session
        async def run_search():
            # Create a new session for this search
            session = await _search_agent_session.create_session(
                state={}, 
                app_name="search_agent_tool", 
                user_id="user"
            )
            
            # Create the user message
            content = types.Content(role="user", parts=[types.Part(text=query)])
            
            # Run the search agent with the query
            events = _search_agent_runner.run(
                session_id=session.id,
                user_id="user",
                new_message=content
            )
            
            # Extract the response from events
            response_text = ""
            for event in events:
                if hasattr(event, 'content') and event.content:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text = part.text
                            break
            
            return response_text if response_text else f"No results found for query: {query}"
        
        # Run the async function
        try:
            loop = asyncio.get_running_loop()
            # If we're already in an async loop, create a task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, run_search())
                result = future.result(timeout=30)
        except RuntimeError:
            # No running loop, safe to use asyncio.run
            result = asyncio.run(run_search())
        
        return result
            
    except Exception as e:
        return f"Error searching with grounding: {str(e)}"
