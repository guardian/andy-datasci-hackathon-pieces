# how to set up iam permissions in GKE

Following from https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#authenticating_to
and https://cloud.google.com/storage/docs/access-control/iam-roles.

Note, the docs say that workload identity federation is enabled by default on autopilot clusters (which this is)

### Get GKE login
```bash
gcloud container clusters get-credentials autopilot-cluster-1 --region europe-west2 --project guardian-hackathon
```
This connects kubectl to the cluster

### Create kubernetes service account
```bash
export K8S_SVC_NAME=hackathon-data-ingest
kubectl create serviceaccount $K8S_SVC_NAME
```

### Identify the project ID and project number
```bash
export GCP_PROJECT=984497589548
export PROJECT_NAME=guardian-hackathon
```

### Assign the storage.objectUser role to the service account
```bash
gcloud projects add-iam-policy-binding projects/$PROJECT_NAME \
--role=roles/storage.objectUser \
--member=principal://iam.googleapis.com/projects/$GCP_PROJECT/locations/global/workloadIdentityPools/$PROJECT_NAME.svc.id.goog/subject/ns/default/sa/$K8S_SVC_NAME \
--condition=None
```

```
ERROR: (gcloud.projects.add-iam-policy-binding) User [andy.gallagher@guardian.co.uk] does not have permission to access projects instance [guardian-hackathon:setIamPolicy] (or it may not exist): Policy update access denied.
```

:'-(
