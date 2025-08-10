# Chauffeur - Cloud Functions Architecture

Scalable serverless architecture for the Chauffeur platform using GCP Cloud Functions.

## 🏗️ Architecture

```
chauffeur/
├── handlers/              # Cloud Functions (new architecture)
│   ├── functions/         # Individual Cloud Functions
│   │   ├── auth/         # Authentication functions
│   │   ├── oauth/        # OAuth functions  
│   │   └── shared/       # Shared utilities
│   ├── client/           # Python client library
│   └── scripts/          # Deployment scripts
├── serverless.yaml        # Serverless configuration
├── package.json           # Node.js dependencies
└── deploy.sh             # Deployment script
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Set Environment Variables
```bash
export FIREBASE_API_KEY="your-firebase-api-key"
export GOOGLE_OAUTH_CLIENT_ID="your-google-oauth-client-id"
```

### 3. Deploy
```bash
npm run deploy
# or
./deploy.sh
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
- `GCP_PROJECT_ID`: GCP project ID (auto-detected)

### serverless.yaml
Main configuration file defining:
- Function handlers and routes
- Environment variables
- GCP resources (secrets, storage)
- Memory, timeout, and scaling settings

## 📈 Monitoring

- **GCP Console**: https://console.cloud.google.com/functions/list
- **Logs**: `npm run logs`
- **Metrics**: Available in GCP Cloud Monitoring

## 🔄 Development

### Add New Functions
1. Create function in `handlers/functions/`
2. Add to `serverless.yaml`
3. Deploy with `npm run deploy`

### Update Functions
```bash
npm run deploy
```

### View Logs
```bash
npm run logs
npm run logs:oauth
npm run logs:user
```

## 🗑️ Cleanup

Remove all deployed resources:
```bash
npm run remove
```

## 📋 serverless.yaml Configuration

### Functions Section
```yaml
functions:
  auth:
    handler: handlers/functions/auth/main.py
    events:
      - http:
          path: /auth/{proxy+}
          method: ANY
    environment:
      FIREBASE_API_KEY: ${env:FIREBASE_API_KEY}
    memory: 256MB
    timeout: 60s
```

### Resources Section
```yaml
resources:
  - name: firebase-api-key-secret
    type: gcp-types/secretmanager-v1:projects.secrets
    properties:
      parent: projects/${env:GCP_PROJECT_ID}
      secretId: firebase-api-key
```

## 🔧 Available Commands

```bash
# Deploy all functions
npm run deploy

# Deploy to specific environment
npm run deploy:prod
npm run deploy:dev

# Remove all functions
npm run remove

# View function info
npm run info

# View logs
npm run logs
npm run logs:oauth
npm run logs:user
```

## 🌐 Function URLs

After deployment, your functions will be available at:
- **Auth**: `https://us-central1-YOUR_PROJECT.cloudfunctions.net/auth`
- **OAuth**: `https://us-central1-YOUR_PROJECT.cloudfunctions.net/oauth`
- **User**: `https://us-central1-YOUR_PROJECT.cloudfunctions.net/user`

## 🆚 Comparison with AWS serverless.yml

| Feature | AWS serverless.yml | GCP serverless.yaml |
|---------|-------------------|---------------------|
| **Provider** | `provider: aws` | `provider: google` |
| **Runtime** | `runtime: nodejs18.x` | `runtime: python310` |
| **Events** | `events: - httpApi` | `events: - http` |
| **Environment** | `environment:` | `environment:` |
| **Resources** | `resources:` | `resources:` |

## 🛠️ Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure you're authenticated with GCP
   ```bash
   gcloud auth application-default login
   ```

2. **Environment Variables Not Set**: Check your exports
   ```bash
   echo $FIREBASE_API_KEY
   echo $GOOGLE_OAUTH_CLIENT_ID
   ```

3. **Function Deployment Fails**: Check logs
   ```bash
   npm run logs
   ```

## 📚 Additional Documentation

- [Secrets Management](handlers/SECRETS_SETUP.md)
- [Client Library Usage](handlers/example_usage.py) 