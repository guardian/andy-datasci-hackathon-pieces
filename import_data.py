#!/usr/bin/env python3

from google.cloud import storage
import os
import pandas as pd
import io
from sentence_transformers import SentenceTransformer
from pprint import pprint
from hackathon.indexing import create_index, send_to_index
import logging

logging.basicConfig(level=logging.ERROR)

logger = logging.getLogger(__name__)
logger.level=logging.DEBUG

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
dims = model.get_sentence_embedding_dimension()
INDEX_NAME = 'hackathon-embeddings-data'

EMBED_FIELD_NAMES = [
    'first_para',
    'clean_trail_text',
    'clean_web_title',
    'body_cleaned',
]

#this is safe if the index already exists
create_index(INDEX_NAME, [f"{x}_vec" for x in EMBED_FIELD_NAMES], dims)

def read_gcs_file(bucket_name, blob_name):
    # Initialize the client
    client = storage.Client()
    
    # Get the bucket
    bucket = client.bucket(bucket_name)
    
    # Get the blob (file) from the bucket
    blob = bucket.blob(blob_name)
    
    # # Download the contents as a string
    # content = blob.download_as_text()
    content = blob.download_as_bytes()

    return content

def embed_and_ingest(row):
    vector_fields = {}
    for fieldname in EMBED_FIELD_NAMES:
        key = f"{fieldname}_vec"
        if fieldname in row:
            vector_fields[key] = model.encode(row[fieldname])

    dictval = row.to_dict() | vector_fields
    send_to_index(INDEX_NAME, row['path'], dictval)

### START MAIN
bucketname = os.environ.get("BUCKETNAME")
filename = os.environ.get("FILENAME")
if bucketname == "":
    print("You must specify a bucket in the BUCKETNAME environment variable")
    os.exit(1)
if filename == "":
    print("You must specify a filename in the FILENAME environment variable")
    os.exit(1)

content = read_gcs_file(bucketname, filename)

df = pd.read_parquet(io.BytesIO(content))

df.apply(embed_and_ingest,  axis=1)