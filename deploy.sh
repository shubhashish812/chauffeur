#!/bin/bash

# Deploy Chauffeur Cloud Functions using serverless.yaml
# Usage: ./deploy.sh [environment]

set -e

ENVIRONMENT=${1:-dev}
PROJECT_ID=$(gcloud config get-value project)

echo "🚀 Deploying Chauffeur Cloud Functions to environment: $ENVIRONMENT"
echo "📁 Project: $PROJECT_ID"

# Check if required environment variables are set
if [ -z "$FIREBASE_API_KEY" ]; then
    echo "❌ Error: FIREBASE_API_KEY environment variable not set"
    echo "   Set it with: export FIREBASE_API_KEY='your-firebase-api-key'"
    exit 1
fi

if [ -z "$GOOGLE_OAUTH_CLIENT_ID" ]; then
    echo "❌ Error: GOOGLE_OAUTH_CLIENT_ID environment variable not set"
    echo "   Set it with: export GOOGLE_OAUTH_CLIENT_ID='your-google-oauth-client-id'"
    exit 1
fi

# Set GCP project ID
export GCP_PROJECT_ID=$PROJECT_ID

echo "✅ Environment variables configured"
echo "   - GCP_PROJECT_ID: $GCP_PROJECT_ID"
echo "   - FIREBASE_API_KEY: [HIDDEN]"
echo "   - GOOGLE_OAUTH_CLIENT_ID: [HIDDEN]"

# Enable required APIs
echo "🔧 Enabling required GCP APIs..."
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable deploymentmanager.googleapis.com

# Deploy using serverless framework
echo "📦 Deploying with serverless framework..."
serverless deploy --stage $ENVIRONMENT

echo "✅ Deployment complete!"
echo ""
echo "🌐 Function URLs:"
echo "   - Auth: https://$REGION-$PROJECT_ID.cloudfunctions.net/auth"
echo "   - OAuth: https://$REGION-$PROJECT_ID.cloudfunctions.net/oauth"
echo "   - User: https://$REGION-$PROJECT_ID.cloudfunctions.net/user"
echo ""
echo "📊 Monitor at: https://console.cloud.google.com/functions/list?project=$PROJECT_ID"
