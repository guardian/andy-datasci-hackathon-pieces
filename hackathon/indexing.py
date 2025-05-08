from opensearchpy import OpenSearch
from opensearchpy.exceptions import RequestError
import os
from urllib.parse import urlparse
import re
import logging

logger = logging.getLogger(__name__)
logger.level = logging.DEBUG

# Keyword fields bypass the analyzer and are treated as exact-match/no-match
KEYWORD_FIELDS = [
    "path",
    "section_id",
    "keyword_tag",
    "keyword_tag_title"
]

# Non-index fields are for output only and can't be searched
NON_INDEX_FIELDS = [
    "featuredImage",
    "previewImage",
]

# Additional text fields
TEXT_FIELDS = [
    "clean_web_title",
    "clean_trail_text",
    "body_cleaned",
]

def get_connection_params(endpoint:str):
    endpoint_parsed = urlparse(endpoint)
    use_ssl = endpoint_parsed[0]=="https"

    splitter = re.compile(r'^(.+):([\d]+)$')
    host_port = splitter.findall(endpoint_parsed[1])

    if host_port:
        hostname = host_port[0][0]
        host_port_num = int(host_port[0][1])
    else:
        hostname = endpoint_parsed[1]
        host_port_num = 9200
        
    return hostname, host_port_num, use_ssl


def build_search_client():
    endpoint = None
    if "OPENSEARCH_ENDPOINT" in os.environ:
        endpoint = os.environ["OPENSEARCH_ENDPOINT"]
        
    if endpoint is None or endpoint=="":
        endpoint = "http://localhost:9200"

    if "://" in endpoint:
        hostname, host_port, use_ssl = get_connection_params(endpoint)
    else:
        hostname = endpoint
        host_port = 443
        use_ssl = True

    ssl_assert_hostname = hostname
    if "SSL_SKIP_VERIFY" in os.environ:
        ssl_assert_hostname = False

    print(f"INFO Opensearch hostname {hostname}, port {host_port}, SSL {use_ssl} SSL assert hostname {ssl_assert_hostname}")

    return OpenSearch(
        hosts=[{'host': hostname, 'port': host_port}],
        http_compress=True,
        use_ssl=use_ssl,
        ssl_assert_hostname=ssl_assert_hostname
    )


client = build_search_client()


def send_to_index(index_name:str, id:str, data_to_index:dict):
    logger.info("Updating {} in the index {}...".format(id, index_name))
    try:
        client.update(
            index=index_name,
            id=id,
            body={
                "doc": data_to_index,
                "doc_as_upsert": True
            },
            refresh=True
        )
        logger.info("Done")
    except Exception as e:
        logger.error("Could not update index: {}".format(str(e)), exc_info=e)
        raise   #re-raise the exception here to fail the lambda so we can retry / DLQ


def delete_from_index(index_name:str, recipe_id:str):
    client.delete(
        index=index_name,
        id=recipe_id
    )


def mapping_definitions(vector_fields:list[str], dims:int)->dict:
    """
    Creates an OpenSearch mapping definition suitable for the given embeddings - only needs to be done at init.
    Why do we need some embeddings before we create? Because Opensearch needs to know the vector dimensions when the field is created.
    See https://opensearch.org/docs/latest/search-plugins/knn/approximate-knn/ for details
    """

    # In general, nmslib outperforms both faiss and Lucene on search. 
    # However, to optimize for indexing throughput, faiss is a good option. 
    # For relatively smaller datasets (up to a few million vectors), the Lucene engine demonstrates better latencies and recall.
    #At the same time, the size of the index is smallest compared to the other engines, which allows it to use smaller 
    # AWS instances for data nodes.
    result = {}
    for fieldname in vector_fields:
        result[fieldname] = {
            'type': 'knn_vector',
            'dimension': dims,
            'method': {
                'name': 'hnsw',
                'space_type': 'cosinesimil',
                'engine': 'lucene',
                # "parameters": {
                #     "ef_construction": 128,
                #     "m": 24
                # }
            }
        }
    if result == {}:
        raise ValueError("No mappings found? This isn't right")
    
    for fieldname in KEYWORD_FIELDS:
        result[fieldname] = {
            'type': 'keyword',
            'index': True,
        }

    for fieldname in NON_INDEX_FIELDS:
        result[fieldname] = {
            'type': 'keyword',
            'index': False,
        }

    for fieldname in TEXT_FIELDS:
        result[fieldname] = {
            'type': 'text',
        }

    return result


def create_index(index_name:str, vector_fields:list[str], dims:int):
    if client.indices.exists(index_name):
        return

    try:
        logger.info("Creating index if necessary...")
        client.indices.create(
            index_name,
            body={
                'settings': {
                    'index': {
                        'number_of_shards': 3,
                        'number_of_replicas': 1,
                        'knn': True,
                    }
                },
                'mappings': {
                    'properties': mapping_definitions(vector_fields, dims)
                }
            }
        )
        logger.info("Created")
    except RequestError as e:   #even though we do an "exists" check at the start, we still need to catch here in case we are in a race-condition
        if e.error=="resource_already_exists_exception":    #ignore if it's already created
            logger.info("Index already existed")
            pass
        else:
            logger.error("could not create index: ", exc_info=e)
            raise e