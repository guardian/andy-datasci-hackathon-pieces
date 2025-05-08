#!/bin/bash

for i in {0..9}; do
cat <<EOF > minilm-indexer-job-$i.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: minilm-indexer-job-$i
spec:
  template:
    spec:
      containers:
      - name: minilm-indexer
        image: eu.gcr.io/guardian-hackathon/andy-minilm-indexer:5
        command: ["python", "/usr/local/bin/import_data.py"]
        env:
        - name: INDEX_NAME
          value: hackathon-embeddings-data
        - name: BUCKETNAME
          value: ag_vector_datasets
        - name: FILENAME
          value: df_gcp_${i}.parquet
        - name: OPENSEARCH_ENDPOINT
          value: http://opensearch:9200
      restartPolicy: Never
  backoffLimit: 3
EOF
done
