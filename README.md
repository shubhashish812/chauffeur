# Chauffeur - Cloud Functions Architecture

Scalable serverless architecture for the Chauffeur platform using GCP Cloud Functions.

## 🏗️ Architecture

```
chauffeur/
├── shared/                    # Shared modules (single source)
│   ├── firebase_client.py     # Firebase client singleton
│   ├── auth_utils.py          # Authentication utilities
│   ├── models.py              # Pydantic models
│   └── __init__.py
├── handlers/                  # All Cloud Functions
│   ├── requirements.txt       # Unified requirements
│   ├── auth/                 # Auth function only
│   │   └── main.py
│   ├── oauth/                # OAuth function only
│   │   └── main.py
│   └── user/                 # User function only
│       └── main.py
├── scripts/                  # Deployment scripts
│   ├── deploy-all.sh         # Deploy all functions
│   ├── deploy-auth.sh        # Deploy auth only
│   ├── deploy-oauth.sh       # Deploy oauth only
│   └── deploy-all.ps1        # PowerShell version
└── README.md
```

## 🚀 Quick Start

### 1. Set Environment Variables
```bash
# PowerShell
$env:FIREBASE_API_KEY = "your-firebase-api-key"
$env:GOOGLE_OAUTH_CLIENT_ID = "your-google-oauth-client-id"

# Bash
export FIREBASE_API_KEY="your-firebase-api-key"
export GOOGLE_OAUTH_CLIENT_ID="your-google-oauth-client-id"
```

### 2. Deploy All Functions
```bash
# PowerShell
.\scripts\deploy-all.ps1

# Bash
./scripts/deploy-all.sh
```

### 3. Deploy Individual Functions
```bash
# PowerShell
.\scripts\deploy-auth.ps1
.\scripts\deploy-oauth.ps1

# Bash
./scripts/deploy-auth.sh
./scripts/deploy-oauth.sh
```

## 📊 Function Endpoints

| Function | Endpoint | Purpose |
|----------|----------|---------|
| `chauffeur-auth` | `/auth/*` | User registration, login, token management |
| `chauffeur-oauth` | `/oauth/*` | Google OAuth authentication |
| `chauffeur-user` | `/user/*` | User profile management |

## 🔧 Configuration

### Environment Variables
- `FIREBASE_API_KEY`: Firebase project API key
- `GOOGLE_OAUTH_CLIENT_ID`: Google OAuth client ID

### Deployment Configuration
- **Runtime**: Python 3.11
- **Memory**: 256MB
- **Timeout**: 60s
- **Max Instances**: 100
- **Region**: us-central1

## 📈 Monitoring

- **GCP Console**: https://console.cloud.google.com/functions/list
- **Logs**: `gcloud functions logs read chauffeur-auth --region us-central1`
- **Metrics**: Available in GCP Cloud Monitoring

## 🔄 Development

### Add New Functions
1. Create function in `handlers/function-name/main.py`
2. Add deployment script in `scripts/`
3. Deploy with `.\scripts\deploy-all.ps1`

### Update Functions
```bash
# Deploy all
.\scripts\deploy-all.ps1

# Deploy specific function
.\scripts\deploy-auth.ps1
```

### View Logs
```bash
gcloud functions logs read chauffeur-auth --region us-central1
gcloud functions logs read chauffeur-oauth --region us-central1
gcloud functions logs read chauffeur-user --region us-central1
```

## 🗑️ Cleanup

Remove all deployed resources:
```bash
gcloud functions delete chauffeur-auth --region us-central1 --quiet
gcloud functions delete chauffeur-oauth --region us-central1 --quiet
gcloud functions delete chauffeur-user --region us-central1 --quiet
```

## 🌐 Function URLs

After deployment, your functions will be available at:
- **Auth**: `https://us-central1-chauffeur-38757.cloudfunctions.net/chauffeur-auth`
- **OAuth**: `https://us-central1-chauffeur-38757.cloudfunctions.net/chauffeur-oauth`
- **User**: `https://us-central1-chauffeur-38757.cloudfunctions.net/chauffeur-user`

## 🎯 Key Features

### Clean Architecture
- **Single Source of Truth**: Shared modules in `shared/` directory
- **No Duplication**: Unified requirements and configuration
- **Modular Design**: Each function is self-contained

### Deployment
- **Automated Scripts**: One-command deployment
- **Cross-Platform**: PowerShell and Bash scripts
- **Environment Validation**: Automatic environment variable checks

### Scalability
- **Serverless**: Auto-scaling based on demand
- **Cost-Effective**: Pay only for actual usage
- **High Availability**: Google Cloud infrastructure

## 🔧 Available Commands

```bash
# Deploy all functions
.\scripts\deploy-all.ps1

# Deploy specific functions
.\scripts\deploy-auth.ps1
.\scripts\deploy-oauth.ps1

# View function info
gcloud functions describe chauffeur-auth --region us-central1

# View logs
gcloud functions logs read chauffeur-auth --region us-central1

# Delete functions
gcloud functions delete chauffeur-auth --region us-central1 --quiet
```

## 🚀 Why This Structure?

### Benefits of the New Architecture:
1. **No Code Duplication**: Shared modules are in one place
2. **Easy Maintenance**: Update shared code once, affects all functions
3. **Clean Separation**: Handlers only contain function logic
4. **Unified Configuration**: Single requirements.txt and deployment scripts
5. **Scalable**: Easy to add new functions following the same pattern

### Why Not Serverless Framework?
- **Plugin Issues**: The Google Cloud plugin has bugs and depends on deprecated services
- **Direct Control**: `gcloud functions deploy` gives more control and reliability
- **Future-Proof**: No dependency on third-party plugins that may break 