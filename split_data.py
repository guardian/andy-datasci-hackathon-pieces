#!/usr/bin/env python3

"""
Takes in a large dataset and splits it into 10 chunks to be run in parallel
"""
import pandas as pd

### START MAIN
data = pd.read_parquet('df_gcp.parquet', engine='fastparquet')
#print(data.iloc[0]["body_cleaned"])
splits = 10

total_len = len(data)
len_per_split = total_len / splits

for x in range(splits):
    start_point = int(x * len_per_split)
    end_point = int((x+1) * len_per_split)
    if end_point > total_len:
        end_point = total_len
    subset = data.iloc[start_point:end_point]
    subset.to_parquet(f'df_gcp_{x}.parquet', engine='fastparquet')