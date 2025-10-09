# WTL HLR/HSS Connector Microservice

FastAPI microservice that processes PortaBilling ESPF events (already processed by NSPS) and synchronizes subscriber data with WTL HLR/HSS system.

## Features

- FastAPI web framework
- Processes PortaBilling ESPF events that have been pre-processed by NSPS
- Synchronizes subscriber data with WTL HLR/HSS system
- Docker containerization
- Health check endpoint
- JSON structured logging with request tracing
- Configuration via environment variables
- Bearer token authentication

## API Endpoints

### Health Check
- **GET** `/health` - Service health status

### Event Processing
- **POST** `/process-event` - Process PortaBilling ESPF events (post-NSPS processing)
  - Requires Bearer authentication
  - Accepts JSON payload with event data

## Installation and Setup

### Using Docker Compose (Recommended)

1. **Configure**:
   ```bash
   cd wtl-hlr-hss-microservice
   cp .env.example .env
   # Edit .env file with your configuration
   ```

2. **Build and run**:
   ```bash
   docker compose up --build
   ```

3. **Check the service**:
   ```bash
   curl http://localhost:8000/health
   ```

### Using Docker

1. **Build the image**:
   ```bash
   docker build -t wtl-hlr-hss-connector .
   ```

2. **Run the container**:
   ```bash
   docker run -p 8000:8000 \
     -e API_TOKEN=your-token \
     -e WTL_API_URL=http://your-wtl-url \
     -e WTL_API_TOKEN=your-wtl-token \
     wtl-hlr-hss-connector
   ```

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r app/requirements.txt
   ```

2. **Set environment variables**:
   ```bash
   export API_TOKEN=your-token
   export WTL_API_URL=http://your-wtl-url
   export WTL_API_TOKEN=your-wtl-token
   # ... other variables
   ```

3. **Run the application**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `API_TOKEN` | Bearer token for API authentication | `your-secure-token` |
| `WTL_API_URL` | WTL API base URL | `http://wtl-api:3001/wtl/hlr/v1` |
| `WTL_API_TOKEN` | WTL API authentication token | `wtl-token` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | `wtl-hlr-hss-connector` |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `DEBUG` | Enable debug mode | `false` |
| `WTL_DEFAULT_CS_PROFILE` | Default CS profile | `default` |
| `WTL_DEFAULT_EPS_PROFILE` | Default EPS profile | `default` |
| `WTL_HTTP_REQUESTS_TIMEOUT` | HTTP timeout for WTL requests | `30.0` |
| `WTL_IMSI_REGEXP` | IMSI validation regex | `None` |

**Note**: When deploying to Google Cloud Run, the `PORT` environment variable is automatically managed by the platform and should not be set manually.

## Usage Example

### Process Event Request

```bash
curl -X POST http://localhost:8000/process-event \
  -H "Authorization: Bearer your-api-token" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "3e84c79f-ab6f-4546-8e27-0b6ab866f1fb",
    "data": {
      "event_type": "SIM/Updated",
      "variables": {
        "i_env": 1,
        "i_event": 999999,
        "i_account": 1,
        "curr_status": "used",
        "prev_status": "active"
      }
    },
    "pb_data": {
      "account_info": {
        "bill_status": "open",
        "billing_model": "credit_account",
        "blocked": false,
        "i_account": 1,
        "i_customer": 6392,
        "i_product": 3774,
        "id": "79123456789@msisdn",
        "phone1": "",
        "product_name": "wtl Pay as you go",
        "time_zone_name": "Europe/Prague",
        "assigned_addons": [
          {
            "addon_effective_from": "2025-05-16T12:59:46",
            "addon_priority": 10,
            "description": "",
            "i_product": 3775,
            "i_vd_plan": 1591,
            "name": "wtl Youtube UHD"
          }
        ],
        "service_features": [
          {
            "name": "netaccess_policy",
            "effective_flag_value": "Y",
            "attributes": [
              {
                "name": "access_policy",
                "effective_value": "179"
              }
            ]
          }
        ]
      },
      "sim_info": {
        "i_sim_card": 3793,
        "imsi": "001010000020349",
        "msisdn": "79123456789",
        "status": "active"
      },
      "access_policy_info": {
        "i_access_policy": 179,
        "name": "WTL integration test",
        "attributes": [
          {
            "group_name": "lte.wtl",
            "name": "cs_profile",
            "value": "cs-pp-20250319"
          },
          {
            "group_name": "lte.wtl",
            "name": "eps_profile",
            "value": "eps-pp-20250319"
          }
        ]
      }
    },
    "handler_id": "p1-nsps",
    "created_at": "2025-03-12T16:47:30.443939+00:00",
    "updated_at": "2025-03-12T16:47:36.585885+00:00",
    "status": "received"
  }'
```

### Response Examples

#### Successful Event Processing
```json
{
  "message": "Event processed successfully"
}
```

#### Event Ignored (No Action)
```json
{
  "message": "Event ignored: No defined action for event type: SIM/Updated"
}
```

#### Event Ignored (Invalid IMSI)
```json
{
  "message": "Event ignored: IMSI is empty or not provided"
}
```

#### Event Ignored (IMSI Validation Failed)
```json
{
  "message": "Event ignored: IMSI 901700000050170 doesn't follow the regexp provided"
}
```

#### Error Response
```json
{
  "message": "Internal server error",
  "error": "Error details..."
}
```

## Monitoring and Logging

- Health checks available at `/health`
- JSON formatted logs (when not in debug mode)
- Request tracing with `x-b3-traceid` and `x-request-id` headers

## Architecture

```
app/
├── main.py              # FastAPI application and routes
├── core/                # Configuration and utilities
│   ├── config.py        # Settings and configuration
│   ├── logging.py       # Logging setup
│   ├── event_processor.py # Event processing utilities
│   └── middleware.py    # Custom middlewares
├── models/              # Data models
│   ├── errors.py        # Error response models
│   ├── events.py        # PortaBilling event models
│   └── wtl.py           # WTL API models
├── services/            # Business logic
│   ├── pb_event.py      # PortaBilling event processor
│   └── wtl_client.py    # WTL API client
└── requirements.txt
```

## Deployment

This microservice supports deployment to multiple cloud platforms. Each platform has its own dedicated deployment scripts and configuration.

Other platforms can also be used for deployment, but currently there are no deployment scripts provided for them.

### Supported Cloud Platforms

| Platform | Service | Status | Scripts Location |
|----------|---------|--------|------------------|
| **Google Cloud Platform** | Cloud Run | ✅ Implemented | `_gcp-deploy/` |
| **Amazon Web Services** | App Runner | ✅ Implemented | `_aws-deploy/` |

### Google Cloud Platform (GCP) Deployment

The microservice can be deployed to Google Cloud Run using the provided GCP deployment scripts located in `_gcp-deploy/` directory.

#### Prerequisites

- [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) installed and configured
- Docker installed (for Cloud Run deployment)
- Authenticated with Google Cloud (`gcloud auth login`)

#### Quick Commands

For Cloud Run:
```bash
# Interactive deployment (recommended)
make gcp-deploy

# Force full redeploy
make gcp-deploy-force

# Update environment variables only (fast)
make gcp-update-env

# View service logs
make gcp-logs

# Check service status
make gcp-status
```

#### Environment Configuration

1. **Set GCP deployment variables**:
   ```bash
   export PROJECT_ID=your-project-id    # Your GCP Project ID
   export REGION=europe-west3           # Optional, defaults to europe-west3
   ```

2. **Create .env file**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Required variables in .env**:
   ```bash
   API_TOKEN=your-secure-api-token
   WTL_API_URL=https://wtl-api.example.com/wtl/hlr/v1
   WTL_API_TOKEN=your-wtl-api-token
   ```

The deployment scripts will automatically load variables from `.env` file and configure the service.

#### How It Works

The deployment scripts:
- ✅ Automatically load configuration from `.env` file
- ✅ Check prerequisites and environment variables
- ✅ Configure gcloud settings and enable required APIs
- ✅ Deploy service with environment variables
- ✅ Test the deployment
- ✅ Provide interactive options for existing services

#### Service Configuration

Cloud Run configuration:
- **Memory**: 512Mi
- **CPU**: 1 vCPU
- **Min instances**: 0 (scales to zero)
- **Max instances**: 10
- **Timeout**: 300 seconds
- **Port**: Automatically managed by Cloud Run
- **Public access**: Enabled

To modify these settings, edit the configuration in the deployment script:
- Cloud Run: `_gcp-deploy/deploy_cloud_run_service.sh`

### Amazon Web Services (AWS) Deployment

The microservice can be deployed to AWS App Runner using the provided AWS deployment scripts located in `_aws-deploy/` directory.

#### Prerequisites

- [AWS CLI](https://aws.amazon.com/cli/) installed and configured
- Docker installed
- AWS account with appropriate permissions

#### Quick Commands

```bash
# Deploy or update service
make aws-deploy

# Test existing service only
make aws-test-only

# Delete service
make aws-destroy
```

#### Environment Configuration

1. **Configure AWS CLI**:
   ```bash
   aws configure
   ```

2. **Set AWS deployment variables**:
   ```bash
   export AWS_ACCOUNT_ID=123456789012  # Your AWS Account ID
   export AWS_REGION=eu-west-1         # Optional, defaults to eu-west-1
   ```

3. **Create .env file**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Required variables in .env**:
   ```bash
   API_TOKEN=your-secure-api-token
   WTL_API_URL=https://wtl-api.example.com/wtl/hlr/v1
   WTL_API_TOKEN=your-wtl-api-token
   ```

The deployment script will automatically load variables from `.env` file and configure the service.

#### How It Works

The deployment script:
- ✅ Automatically loads configuration from `.env` file
- ✅ Checks prerequisites and AWS authentication
- ✅ Creates ECR repository with security scanning
- ✅ Builds and pushes Docker image to ECR
- ✅ Creates IAM roles for App Runner ECR access
- ✅ Deploys service with auto scaling configuration
- ✅ Tests the deployment with health checks
- ✅ Provides options for testing and service management

#### Service Configuration

The deployment configures App Runner with:
- **Memory**: 0.5 GB
- **CPU**: 0.25 vCPU
- **Min instances**: 0 (scale-to-zero) ⚡
- **Max instances**: 3
- **Concurrency**: 100 requests per instance
- **Port**: 8000 (automatically detected)
- **Public access**: Enabled with HTTPS

To modify these settings, edit the configuration variables at the beginning of `_aws-deploy/deploy_apprunner.sh`.