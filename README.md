# What's in this repo?

1. My backup vectorisation kahuna.  This consists of some Kubernetes manifests (under `kube`) to deploy Opensearch and a batch
of vectorisation jobs that talk to it.  The intention is to deploy these into a GKE kubernetes cluster; other clusters will
work but you'll need to check out the storage class and make sure that is appropriate.

To talk to the index, you'll need to set up a local port-forward: 
```bash
kubectl port-forward svc/opensearch 9200:9200
```

2. Source code and Dockerfile build for the vectorisation job (in the root).  This consists of two python programs:
 - `split_data.py` - run this to take large data dump in parquet format and split it into a number of smaller dumps for parallel processing
 - `import_data.py` - run this to take a (smaller) data dump from a GCS bucket, vectorise and output it into the Opensearch cluster
 - `Dockerfile` - run `docker build .` in the root to bundle the python scripts into a container.  This is then used by the jobs under `kube/imports` to do the actual import.  There is a simple shell script in `kube/imports` which sets up a set of 10 of these jobs to run on 10 data files in parallel
 - `requirements.txt`  - requirements file for the vectorisation jobs

3. Source code for the AI conversation agent that I demoed, under `vertex-agent`.  This has its own `requirements.txt` in the
`vertex-agent` directory and it depends on Google's Agent Development Kit (adk).  To run this, once you've installed the
requirements into your virtualenv run this command _from the root of the repo_:

```bash
adk web
```

This will start up the server on local port 8000.  Go to http://localhost:8000 in a browser and select `vertex-agent` from the blue dropdown on the left marked "Select agent".  You can then converse with it.
