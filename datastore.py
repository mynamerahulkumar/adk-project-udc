import os
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Definition of a tool that accesses a Vertex AI Search Datastore

#
# This is based on code provided by Google at
# https://cloud.google.com/generative-ai-app-builder/docs/samples/genappbuilder-search
#
# The object definitions aren't available to all IDEs because of Google's ProtoBuf
# implementation, so the IDE may generate a warning, but work fine. I've used
# dicts here instead, but indicated the Class that could be used instead.
# You can see the definitions at
# https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1.types
#
def search(
    project_id: str,
    location: str,
    engine_id: str,
    search_query: str,
) -> list[str]:
    """
    Search the Vertex AI Search datastore for information.
    
    Args:
        project_id: Google Cloud project ID
        location: Location of the search engine (e.g., 'global')
        engine_id: ID of the search engine/datastore
        search_query: The search query string
    
    Returns:
        List of formatted search results
    """
    #  For more information, refer to:
    # https://cloud.google.com/generative-ai-app-builder/docs/locations#specify_a_multi-region_for_your_data_store
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )

    # Create a client
    client = discoveryengine.SearchServiceClient(client_options=client_options)

    # The full resource name of the search app serving config
    serving_config = f"projects/{project_id}/locations/{location}/collections/default_collection/engines/{engine_id}/servingConfigs/default_config"

    # Build the search request
    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=search_query,
        page_size=5,
        content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
            snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                return_snippet=True,
                max_snippet_length=200,
            ),
            summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                summary_result_count=3,
                include_citations=True,
            ),
        ),
    )

    # Execute the search
    page_result = client.search(request)

    # Format and return the results
    results = []
    for result in page_result.results:
        if hasattr(result, 'document'):
            doc = result.document
            title = doc.title if hasattr(doc, 'title') else "Unknown"
            
            # Extract content from the document
            content = ""
            if hasattr(doc, 'struct_data'):
                struct_data = doc.struct_data
                if 'text' in struct_data:
                    content = struct_data['text']
                elif 'content' in struct_data:
                    content = struct_data['content']
                else:
                    content = " ".join(str(v) for v in struct_data.values() if v)
            
            if content:
                results.append(f"Source: {title}\nContent: {content}")
    
    return results if results else ["No results found."]


def search_documents(query: str) -> str:
    """
    Tool function that searches documents using Vertex AI Search.
    Falls back to hardcoded information if Vertex AI is not configured.
    
    Args:
        query: The search query to find in the documents
    
    Returns:
        Formatted string with search results or fallback information
    """
   
    
    try:
        # Get configuration from environment
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
        datastore_id = os.getenv("DATASTORE_ID", "").split("/dataStores/")[-1]
        
        # Try Vertex AI Search if configured
        if project_id and datastore_id:
            try:
                # Perform the search
                results = search(
                    project_id=project_id,
                    location=location,
                    engine_id=datastore_id,
                    search_query=query,
                )
                
                # # Format results for the agent
                # if not results or (len(results) == 1 and "No results" in results[0]):
                #     # Fall back to fallback info if no search results
                #     return _get_fallback_response(query, fallback_info)
                
                formatted_results = "\n\n".join(results)
                return f"Found the following information:\n\n{formatted_results}"
            except Exception as e:
                # If Vertex AI fails, use fallback
                print(f"Vertex AI Search failed: {str(e)}")
                
        
            
    except Exception as e:
        # Ultimate fallback
        print("Exception as e",e)
