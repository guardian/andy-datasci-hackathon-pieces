#!/usr/bin/env python3

from google.cloud import bigquery
from pprint import pprint
import pandas as pd
import pandas_gbq

client = bigquery.Client()

project = "guardian-hackathon"
dataset_id = "embeddings_hack"
#table_id = "text-embedding-005_body_cleaned_tmp"
location = "europe-west2"
table_id_list = [
    "text-embedding-004_body_cleaned_tmp",
    "text-embedding-004_cleaned_trail_text_tmp",
    "text-embedding-004_cleaned_web_title_tmp",
    "text-embedding-004_first_para_tmp",
    "content_new_sample_processed",
    "lf_gu_article",
    "lf_gu_article_endpoint",
    "lf_gu_article_vecs"
]

for table_id in table_id_list:
    q = f"""SELECT * from `{dataset_id}.{table_id}`"""
    #result = client.query(q, location=location)

    df = pandas_gbq.read_gbq(q)
    # pprint(df.columns)
    df.to_parquet(f"{table_id}.parquet",engine="pyarrow",compression="gzip")