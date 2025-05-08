import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent
import requests
import os
from google import genai
from google.cloud import aiplatform
import tqdm
import time
import numpy as np
import pandas as pd


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
    CapiKey = os.environ.get("CAPI_KEY") or "test"

    print(f"Looking up {path}...")
    url = f"https://content.guardianapis.com/{path}?api-key={CapiKey}&show-fields=all"
    response = requests.get(url)
    if response.status_code==200:
        response_body = response.json()
        print(response_body)
        return {
            "status": "success",
            "headline": response_body["response"]["content"]["fields"]["headline"],
            "article_text": response_body["response"]["content"]["fields"]["bodyText"],
            "published": response_body["response"]["content"]["fields"]["firstPublicationDate"],
        }
    else:
        error = response.text
        return {
            "status": "error",
            "error": error
        }
    
BATCH_SIZE=5
def get_embeddings_wrapper(texts: list[str]) -> list[list[float]]:
    embeddings: list[list[float]] = []
    for i in tqdm.tqdm(range(0, len(texts), BATCH_SIZE)):
        time.sleep(1)  # to avoid the quota error
        response = client.models.embed_content(
            model=TEXT_EMBEDDING_MODEL_ID, contents=texts[i : i + BATCH_SIZE]
        )
        embeddings = embeddings + [e.values for e in response.embeddings]
    return embeddings

# Cross-reference the match IDs that Vertex gives us to paths
def load_data():
    return pd.read_csv('headlines.csv')

df = load_data()

def search_for_news(query: str) -> dict:
    """Search for news on then web
    
    Args:
      query (str): what you're searching for. For example, "What's happening in Pakistan?" or "Why are things so expensive right now?"

    Returns:
      a dict giving success/failure status and a list of article paths
    """

    # === GET EMBEDDING ===
    query_embeddings = get_embeddings_wrapper([query])

    # === MATCHING ENGINE SEARCH ===
    response = index_endpoint.find_neighbors(
        deployed_index_id=DEPLOYED_INDEX_ID,
        queries=query_embeddings,
        num_neighbors=10,
    )
    matching_paths = []

    for idx, neighbor in enumerate(response[0]):
        match_id = np.int64(neighbor.id)
        similar = df.query("id == @match_id", engine="python")
        matching_paths.append({
            "path": similar.path.values[0],
            "score": neighbor.distance,
        })
    
    return {
        "status": "success",
        "articles": matching_paths,
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
    tools=[get_from_guardian, search_for_news],
)