import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent
import requests
import os
from google import genai
from google.cloud import aiplatform

# ==== Google connection
PROJECT_ID = "guardian-hackathon"  # @param {type: "string", placeholder: "[your-project-id]", isTemplate: true}
if not PROJECT_ID or PROJECT_ID == "[your-project-id]":
    PROJECT_ID = str(os.environ.get("GOOGLE_CLOUD_PROJECT"))

LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "europe-west2")


client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
# ==========

INDEX_ENDPOINT_ID = "1312465039843655680"
INDEX_ENDPOINT_NAME = f"projects/{PROJECT_ID}/locations/{LOCATION}/indexEndpoints/{INDEX_ENDPOINT_ID}"



# initialise clients
aiplatform.init(project=PROJECT_ID, location=LOCATION)
index_endpoint = aiplatform.MatchingEngineIndexEndpoint(index_endpoint_name=INDEX_ENDPOINT_NAME)
DEPLOYED_INDEX_ID = "headlines_vector_search_ab_1746702595145"
TEXT_EMBEDDING_MODEL_ID = "text-embedding-005"  # @param {type: "string"}

def get_from_guardian(path: str) -> dict:
    """
    Retrives a full article from the Guardian.

    Args:
      path (str) - the article path to look up. This must be a valid path found via search
    """
    CapiKey = os.environ["CAPI_KEY"] or "test"

    url = f"https://content.guardianapis.com/{path}?api-key={CapiKey}&show-fields=all"
    response = requests.get(url)
    if response.status_code==200:
        response_body = response.json()
        return {
            "status": "success",
            "headline": response_body["response"]["content"]["fields"]["headline"],
            "article_text": response_body["response"]["content"]["fields"]["bodyText"],
            "published": response_body["response"]["content"]["fields"]["firstPublicationDate"],
        }
    else:
        error = response.text()
        return {
            "status": "error",
            "error": error
        }
    
root_agent = Agent(
    name="news_agent",
    model="gemini-2.0-flash",
    description=(
        "Agent to find and summarise relevant news articles"
    ),
    instruction=(
        "You are a helpful agent who can search for content on the Guardian to help explain a complex and disturbing world to the huddled masses"
    ),
    tools=[get_from_guardian],
)