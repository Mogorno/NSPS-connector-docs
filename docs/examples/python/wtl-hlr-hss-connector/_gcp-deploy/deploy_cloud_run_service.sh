#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="wtl-hlr-hss-connector"
MEMORY="512Mi"
CPU="1"
MIN_INSTANCES="0"
MAX_INSTANCES="10"
TIMEOUT="300"
PORT="8000"

# GCP Configuration - get from environment or use defaults
PROJECT_ID="${PROJECT_ID:-}"     # Must be provided by user
REGION="${REGION:-europe-west3}" # Default to europe-west3
REPOSITORY_NAME=connectors

# Function to load environment variables from .env file
load_env_file() {
    local env_file=""

    # Look for .env file in current directory first, then parent directory
    if [ -f ".env" ]; then
        env_file=".env"
    elif [ -f "../.env" ]; then
        env_file="../.env"
    fi

    if [ -n "$env_file" ]; then
        print_message "Loading application variables from $env_file"

        # Export variables from .env file, excluding comments and empty lines
        while IFS= read -r line || [ -n "$line" ]; do
            # Skip comments and empty lines
            if [[ "$line" =~ ^[[:space:]]*# ]] || [[ "$line" =~ ^[[:space:]]*$ ]]; then
                continue
            fi

            # Export the variable if it's not already set
            if [[ "$line" =~ ^[[:space:]]*([^=]+)=(.*)$ ]]; then
                var_name="${BASH_REMATCH[1]}"
                var_value="${BASH_REMATCH[2]}"

                # Remove any trailing spaces and comments from the variable name
                var_name=$(echo "$var_name" | sed 's/[[:space:]]*$//')

                # Only set if not already defined in environment
                if [ -z "${!var_name}" ]; then
                    export "$var_name"="$var_value"
                    print_message "Loaded: $var_name"
                else
                    print_message "Using existing: $var_name (from environment)"
                fi
            fi
        done < "$env_file"

        print_success "Application variables loaded from $env_file"
    else
        print_warning "No .env file found in current or parent directory"
        print_message "You can create .env file based on .env.example"
    fi
}

# Function to print colored messages
print_message() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check required environment variables
check_env_vars() {
    print_message "Checking required environment variables..."

    # Check GCP deployment variables (not from .env file)
    if [ -z "$PROJECT_ID" ]; then
        print_error "PROJECT_ID environment variable is required"
        print_message "Set it with: export PROJECT_ID=your-project-id"
        print_message "Or add it to your shell profile"
        exit 1
    fi

    print_success "Environment variables are set"
    print_message "PROJECT_ID: $PROJECT_ID (deployment)"
    print_message "REGION: $REGION (deployment)"
}

# Check required tools
check_tools() {
    print_message "Checking required tools..."

    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed"
        exit 1
    fi

    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi

    print_success "Required tools are available"
}

# Configure gcloud
configure_gcloud() {
    print_message "Configuring gcloud..."

    gcloud config set project $PROJECT_ID
    gcloud config set run/region $REGION

    # Enable required APIs
    print_message "Enabling required APIs..."
    gcloud services enable run.googleapis.com
    gcloud services enable containerregistry.googleapis.com

    print_success "gcloud configured"
}

# Build and push Docker image
build_and_push() {

    # Create Artifact Registry repository
    print_message "Creating Artifact Registry repository..."
    if ! gcloud artifacts repositories describe "${REPOSITORY_NAME}" \
        --location="${REGION}" \
        --project="${PROJECT_ID}" &>/dev/null; then
        echo "Repository '${REPOSITORY_NAME}' does not exist. Creating..."
        gcloud artifacts repositories create "${REPOSITORY_NAME}" \
            --repository-format=docker \
            --location="${REGION}" \
            --project="${PROJECT_ID}"
    else
        echo "Repository '${REPOSITORY_NAME}' already exists. Skipping creation."
    fi

    print_message "Configure docker credentials..."
    gcloud auth configure-docker ${REGION}-docker.pkg.dev

    print_message "Building Docker image..."

    # Create image name dynamically after PROJECT_ID is loaded
    local IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}/${SERVICE_NAME}"

    docker build -t $IMAGE_NAME .

    print_message "Pushing image to Google Container Registry..."
    docker push $IMAGE_NAME

    print_success "Image built and pushed successfully"

    # Export IMAGE_NAME for use in deploy_service function
    export IMAGE_NAME
}

# Check if service exists
check_service_exists() {
    if gcloud run services describe $SERVICE_NAME --region=$REGION &>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Update environment variables only
update_env_vars_only() {
    print_message "Updating environment variables for existing service..."

    # Build environment variables string
    local env_vars=""
    local required_vars=("API_TOKEN" "WTL_API_URL" "WTL_API_TOKEN")
    local optional_vars=("APP_NAME" "LOG_LEVEL" "DEBUG" "WTL_DEFAULT_CS_PROFILE" "WTL_DEFAULT_EPS_PROFILE" "WTL_HTTP_REQUESTS_TIMEOUT" "WTL_IMSI_REGEXP")
    local missing_required=()

    # Check required variables
    for var in "${required_vars[@]}"; do
        if [ -n "${!var}" ]; then
            if [ -n "$env_vars" ]; then
                env_vars="${env_vars},"
            fi
            env_vars="${env_vars}${var}=${!var}"
        else
            missing_required+=("$var")
        fi
    done

    # Add optional variables if they exist
    for var in "${optional_vars[@]}"; do
        if [ -n "${!var}" ]; then
            if [ -n "$env_vars" ]; then
                env_vars="${env_vars},"
            fi
            env_vars="${env_vars}${var}=${!var}"
        fi
    done

    # Check if we have required variables
    if [ ${#missing_required[@]} -gt 0 ]; then
        print_error "Missing required environment variables: ${missing_required[*]}"
        print_message "Cannot update service without required variables"
        exit 1
    fi

    if [ -n "$env_vars" ]; then
        print_message "Updating Cloud Run service with environment variables..."
        gcloud run services update $SERVICE_NAME \
            --region=$REGION \
            --set-env-vars="$env_vars" \
            --quiet

        print_success "Environment variables updated successfully"
    else
        print_warning "No environment variables found to set"
    fi
}

# Deploy to Cloud Run
deploy_service() {
    print_message "Deploying service to Cloud Run..."

    # Check if IMAGE_NAME is set (should be set by build_and_push function)
    if [ -z "$IMAGE_NAME" ]; then
        IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}/${SERVICE_NAME}"
    fi

    # Build environment variables string for initial deployment
    local env_vars=""
    local required_vars=("API_TOKEN" "WTL_API_URL" "WTL_API_TOKEN")
    local optional_vars=("APP_NAME" "LOG_LEVEL" "DEBUG" "WTL_DEFAULT_CS_PROFILE" "WTL_DEFAULT_EPS_PROFILE" "WTL_HTTP_REQUESTS_TIMEOUT" "WTL_IMSI_REGEXP")
    local missing_required=()

    # Check required variables
    for var in "${required_vars[@]}"; do
        if [ -n "${!var}" ]; then
            if [ -n "$env_vars" ]; then
                env_vars="${env_vars},"
            fi
            env_vars="${env_vars}${var}=${!var}"
        else
            missing_required+=("$var")
        fi
    done

    # Add optional variables if they exist
    for var in "${optional_vars[@]}"; do
        if [ -n "${!var}" ]; then
            if [ -n "$env_vars" ]; then
                env_vars="${env_vars},"
            fi
            env_vars="${env_vars}${var}=${!var}"
        fi
    done

    # Deploy with environment variables if we have the required ones
    if [ ${#missing_required[@]} -eq 0 ] && [ -n "$env_vars" ]; then
        print_message "Deploying with environment variables..."
        gcloud run deploy $SERVICE_NAME \
            --image $IMAGE_NAME \
            --platform managed \
            --region $REGION \
            --memory $MEMORY \
            --cpu $CPU \
            --min-instances $MIN_INSTANCES \
            --max-instances $MAX_INSTANCES \
            --timeout $TIMEOUT \
            --port $PORT \
            --allow-unauthenticated \
            --set-env-vars="$env_vars" \
            --quiet
    else
        print_warning "Deploying without environment variables - service may fail to start"
        if [ ${#missing_required[@]} -gt 0 ]; then
            print_warning "Missing required variables: ${missing_required[*]}"
        fi
        gcloud run deploy $SERVICE_NAME \
            --image $IMAGE_NAME \
            --platform managed \
            --region $REGION \
            --memory $MEMORY \
            --cpu $CPU \
            --min-instances $MIN_INSTANCES \
            --max-instances $MAX_INSTANCES \
            --timeout $TIMEOUT \
            --port $PORT \
            --allow-unauthenticated \
            --quiet
    fi

    print_success "Service deployed successfully"
}

# Get service URL
get_service_url() {
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
    print_success "Service URL: $SERVICE_URL"
    print_message "Health check: $SERVICE_URL/health"
}

# Test deployment
test_deployment() {
    print_message "Testing deployment..."

    if command -v curl &> /dev/null; then
        if curl -s "$SERVICE_URL/health" > /dev/null; then
            print_success "Health check passed"
        else
            print_warning "Health check failed - service might still be starting"
        fi
    else
        print_warning "curl not available - skipping health check"
    fi
}

# Main deployment function
main() {
    local mode="auto"
    local force_deploy=false

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --env-only)
                mode="env-only"
                shift
                ;;
            --force-deploy)
                force_deploy=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    echo "======================================"
    echo " WTL HLR/HSS Connector Deployment"
    echo "======================================"

    load_env_file
    check_env_vars
    check_tools
    configure_gcloud

    # Check if service exists and determine what to do
    if check_service_exists; then
        print_message "Service $SERVICE_NAME already exists in region $REGION"

        if [ "$mode" = "env-only" ]; then
            print_message "Running in environment variables only mode"
            update_env_vars_only
            get_service_url
            test_deployment
        elif [ "$force_deploy" = true ]; then
            print_message "Force deploy requested - rebuilding and redeploying"
            build_and_push
            deploy_service
            get_service_url
            test_deployment
        else
            print_message "Service exists. Choose what to do:"
            echo "1) Update environment variables only (faster)"
            echo "2) Full redeploy with new image (slower)"
            echo "3) Exit"
            read -p "Enter your choice (1-3): " choice

            case $choice in
                1)
                    update_env_vars_only
                    get_service_url
                    test_deployment
                    ;;
                2)
                    build_and_push
                    deploy_service
                    get_service_url
                    test_deployment
                    ;;
                3)
                    print_message "Deployment cancelled"
                    exit 0
                    ;;
                *)
                    print_error "Invalid choice"
                    exit 1
                    ;;
            esac
        fi
    else
        print_message "Service $SERVICE_NAME does not exist - creating new service"
        build_and_push
        deploy_service
        get_service_url
        test_deployment
    fi

    echo ""
    echo "======================================"
    print_success "Operation completed successfully!"
    echo "======================================"
    print_message "Service Name: $SERVICE_NAME"
    print_message "Service URL: $SERVICE_URL"
    print_message "Region: $REGION"
    print_message "Project: $PROJECT_ID"
    echo ""
    if [ -f ".env" ] || [ -f "../.env" ]; then
        print_success "Environment variables were automatically loaded from .env file"
    else
        print_warning "No .env file found. You may need to set environment variables manually:"
        print_warning "- API_TOKEN"
        print_warning "- WTL_API_URL"
        print_warning "- WTL_API_TOKEN"
        print_warning "- Other optional variables as needed"
        echo ""
        print_message "To update environment variables manually:"
        print_message "gcloud run services update $SERVICE_NAME --region=$REGION --set-env-vars=KEY=VALUE"
    fi
}

# Show usage information
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Deploy WTL HLR/HSS Connector to Google Cloud Run"
    echo ""
    echo "Options:"
    echo "  --env-only       Update environment variables only (skip build/deploy)"
    echo "  --force-deploy   Force full redeploy even if service exists"
    echo "  -h, --help       Show this help message"
    echo ""
    echo "Interactive mode:"
    echo "  If service exists and no options specified, script will ask what to do"
    echo ""
    echo "Required environment variables (can be loaded from .env file):"
    echo "  PROJECT_ID       - Google Cloud Project ID"
    echo "  REGION          - Google Cloud Region"
    echo "  API_TOKEN       - Bearer token for API authentication"
    echo "  WTL_API_URL     - WTL API base URL"
    echo "  WTL_API_TOKEN   - WTL API authentication token"
    echo ""
    echo "Examples:"
    echo "  $0                     # Interactive mode"
    echo "  $0 --env-only         # Update environment variables only"
    echo "  $0 --force-deploy     # Force full redeploy"
}

# Run main function
main "$@"
