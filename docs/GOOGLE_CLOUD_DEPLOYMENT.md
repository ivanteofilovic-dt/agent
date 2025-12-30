# Google Cloud Deployment Guide

This guide outlines all Google Cloud services and APIs required to deploy the Combined Agent Platform on Google Cloud.

## Architecture Overview

The application consists of:
1. **Streamlit Web UI** - User interface for both agents
2. **Agent Backend** - Python services for processing
3. **Google ADK Integration** - Agent Development Kit for Google Cloud agents
4. **External API Integrations** - Anthropic, Salesforce, Slack

## Required Google Cloud Services

### 1. **Vertex AI (AI Platform)**
**Purpose**: Host and manage AI agents via Agent Development Kit (ADK)

**APIs to Enable**:
- `aiplatform.googleapis.com` - Vertex AI API
- `aiplatform.googleapis.com/agent-engines` - Agent Builder API

**Required For**:
- Deploying agents as Google Cloud agents
- Agent management and orchestration
- Tool registration and execution

**Setup**:
```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable aiplatform.googleapis.com/agent-engines
```

---

### 2. **Cloud Run**
**Purpose**: Host the Streamlit web application

**APIs to Enable**:
- `run.googleapis.com` - Cloud Run API
- `cloudbuild.googleapis.com` - Cloud Build API (for container builds)

**Required For**:
- Deploying the Streamlit web UI
- Serverless container hosting
- Auto-scaling based on traffic

**Setup**:
```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

---

### 3. **Cloud Storage**
**Purpose**: Store uploaded files (PDFs, DOCX, transcripts)

**APIs to Enable**:
- `storage-api.googleapis.com` - Cloud Storage JSON API
- `storage-component.googleapis.com` - Cloud Storage component

**Required For**:
- Storing uploaded transcript files
- Temporary file storage during processing
- Potential caching of processed data

**Setup**:
```bash
gcloud services enable storage-api.googleapis.com
gcloud services enable storage-component.googleapis.com
```

---

### 4. **Secret Manager**
**Purpose**: Securely store API keys and credentials

**APIs to Enable**:
- `secretmanager.googleapis.com` - Secret Manager API

**Required For**:
- Storing `ANTHROPIC_API_KEY`
- Storing Salesforce OAuth credentials:
  - `SALESFORCE_CLIENT_ID`
  - `SALESFORCE_CLIENT_SECRET`
  - `SALESFORCE_REFRESH_TOKEN`
  - `SALESFORCE_INSTANCE_URL`
- Storing Slack credentials (if using):
  - `SLACK_BOT_TOKEN`
  - `SLACK_SIGNING_SECRET`
  - `SLACK_APP_TOKEN`

**Setup**:
```bash
gcloud services enable secretmanager.googleapis.com
```

---

### 5. **Cloud Logging**
**Purpose**: Application logging and monitoring

**APIs to Enable**:
- `logging.googleapis.com` - Cloud Logging API

**Required For**:
- Application logs
- Error tracking
- Performance monitoring
- Audit trails

**Setup**:
```bash
gcloud services enable logging.googleapis.com
```

---

### 6. **Cloud Monitoring**
**Purpose**: Metrics and alerting

**APIs to Enable**:
- `monitoring.googleapis.com` - Cloud Monitoring API

**Required For**:
- Application metrics
- Performance dashboards
- Alerting on errors or performance issues

**Setup**:
```bash
gcloud services enable monitoring.googleapis.com
```

---

### 7. **Cloud IAM**
**Purpose**: Identity and access management

**APIs to Enable**:
- `iam.googleapis.com` - Identity and Access Management API
- `iamcredentials.googleapis.com` - IAM Service Account Credentials API

**Required For**:
- Service account management
- Permission management
- Secure access to other services

**Setup**:
```bash
gcloud services enable iam.googleapis.com
gcloud services enable iamcredentials.googleapis.com
```

---

### 8. **Cloud Functions or Cloud Tasks** (Optional)
**Purpose**: Background job processing

**APIs to Enable** (if using):
- `cloudfunctions.googleapis.com` - Cloud Functions API
- `cloudtasks.googleapis.com` - Cloud Tasks API

**Required For** (if needed):
- Asynchronous transcript processing
- Scheduled tasks
- Queue management

**Setup** (if needed):
```bash
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudtasks.googleapis.com
```

---

### 9. **Artifact Registry** (Recommended)
**Purpose**: Store container images

**APIs to Enable**:
- `artifactregistry.googleapis.com` - Artifact Registry API

**Required For**:
- Storing Docker container images
- Version control for deployments

**Setup**:
```bash
gcloud services enable artifactregistry.googleapis.com
```

---

### 10. **Cloud SQL or Firestore** (Optional - for future features)
**Purpose**: Database storage (if needed for analytics, user data, etc.)

**APIs to Enable** (if using):
- `sqladmin.googleapis.com` - Cloud SQL Admin API
- `firestore.googleapis.com` - Cloud Firestore API

**Required For** (if needed):
- Storing user preferences
- Analytics data
- Historical transcript data

**Setup** (if needed):
```bash
gcloud services enable sqladmin.googleapis.com
# OR
gcloud services enable firestore.googleapis.com
```

---

## Complete API Enablement Script

Run this script to enable all required APIs:

```bash
#!/bin/bash

# Set your project ID
PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable all required APIs
echo "Enabling Google Cloud APIs..."

# Core services
gcloud services enable aiplatform.googleapis.com
gcloud services enable aiplatform.googleapis.com/agent-engines
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable storage-api.googleapis.com
gcloud services enable storage-component.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable iam.googleapis.com
gcloud services enable iamcredentials.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Optional services (uncomment if needed)
# gcloud services enable cloudfunctions.googleapis.com
# gcloud services enable cloudtasks.googleapis.com
# gcloud services enable sqladmin.googleapis.com
# gcloud services enable firestore.googleapis.com

echo "All APIs enabled!"
```

---

## Service Account Setup

Create service accounts with appropriate permissions:

### 1. Cloud Run Service Account
```bash
# Create service account
gcloud iam service-accounts create combined-agent-sa \
    --display-name="Combined Agent Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:combined-agent-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:combined-agent-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:combined-agent-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

### 2. Vertex AI Service Account
```bash
# Create service account for Vertex AI
gcloud iam service-accounts create vertex-ai-sa \
    --display-name="Vertex AI Service Account"

# Grant Vertex AI permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:vertex-ai-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.admin"
```

---

## Secret Manager Setup

Store all sensitive credentials in Secret Manager:

```bash
# Store Anthropic API key
echo -n "your-anthropic-api-key" | gcloud secrets create anthropic-api-key \
    --data-file=- \
    --replication-policy="automatic"

# Store Salesforce credentials
echo -n "your-client-id" | gcloud secrets create salesforce-client-id \
    --data-file=- \
    --replication-policy="automatic"

echo -n "your-client-secret" | gcloud secrets create salesforce-client-secret \
    --data-file=- \
    --replication-policy="automatic"

echo -n "your-refresh-token" | gcloud secrets create salesforce-refresh-token \
    --data-file=- \
    --replication-policy="automatic"

echo -n "https://yourinstance.salesforce.com" | gcloud secrets create salesforce-instance-url \
    --data-file=- \
    --replication-policy="automatic"

# Store Slack credentials (if using)
echo -n "xoxb-your-token" | gcloud secrets create slack-bot-token \
    --data-file=- \
    --replication-policy="automatic"

echo -n "your-signing-secret" | gcloud secrets create slack-signing-secret \
    --data-file=- \
    --replication-policy="automatic"
```

---

## Cloud Storage Bucket Setup

Create buckets for file storage:

```bash
# Create bucket for uploaded files
gsutil mb -p $PROJECT_ID -l us-central1 gs://$PROJECT_ID-uploads

# Create bucket for processed data (optional)
gsutil mb -p $PROJECT_ID -l us-central1 gs://$PROJECT_ID-processed

# Set lifecycle policies (optional - auto-delete old files)
gsutil lifecycle set lifecycle.json gs://$PROJECT_ID-uploads
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Google Cloud                         │
│                                                          │
│  ┌──────────────┐      ┌──────────────────┐            │
│  │  Cloud Run   │      │   Vertex AI      │            │
│  │  (Streamlit) │◄─────┤  Agent Builder   │            │
│  │              │      │  (ADK Agents)    │            │
│  └──────┬───────┘      └──────────────────┘            │
│         │                                                │
│         ├──────────────┐                                │
│         │              │                                │
│  ┌──────▼──────┐  ┌────▼──────────┐                    │
│  │   Secret     │  │   Cloud       │                    │
│  │   Manager    │  │   Storage     │                    │
│  └─────────────┘  └────────────────┘                    │
│                                                          │
│  ┌──────────────────────────────────────┐               │
│  │   Cloud Logging & Monitoring         │               │
│  └──────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────┘
         │                    │
         │                    │
    ┌────▼────┐          ┌────▼────┐
    │Anthropic│          │Salesforce│
    │  API    │          │   API   │
    └─────────┘          └─────────┘
```

---

## Cost Estimation

Approximate monthly costs (varies by usage):

| Service | Estimated Cost |
|---------|---------------|
| Cloud Run | $0.40 per million requests + compute time |
| Vertex AI | Pay per use (agent invocations) |
| Cloud Storage | $0.020 per GB stored |
| Secret Manager | $0.06 per secret version |
| Cloud Logging | First 50GB free, then $0.50/GB |
| Cloud Monitoring | Free tier: 150MB metrics |

**Note**: Costs depend heavily on usage volume. Use Google Cloud Pricing Calculator for accurate estimates.

---

## Next Steps

1. **Enable all APIs** using the script above
2. **Set up service accounts** with appropriate permissions
3. **Store secrets** in Secret Manager
4. **Create Cloud Storage buckets** for file storage
5. **Deploy Streamlit app** to Cloud Run
6. **Register agents** with Vertex AI Agent Builder
7. **Configure monitoring and alerts**

For detailed deployment instructions, see the deployment scripts in the repository.

---

## Additional Resources

- [Vertex AI Agent Builder Documentation](https://cloud.google.com/vertex-ai/docs/agent-builder)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Cloud Storage Documentation](https://cloud.google.com/storage/docs)

