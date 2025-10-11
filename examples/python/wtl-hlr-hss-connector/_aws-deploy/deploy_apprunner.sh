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
IMAGE_REPOSITORY="wtl-hlr-hss-connector"
CONTAINER_PORT="8000"
CPU="0.25 vCPU"
MEMORY="0.5 GB"
MIN_SIZE="0"
MAX_SIZE="3"
MAX_CONCURRENCY="100"

# Generate unique image tag for each build (date + time)
# This ensures App Runner always pulls the new image on update,
# avoiding ECR/App Runner caching issues with the same tag (e.g., 'latest')
IMAGE_TAG="$(date +%Y%m%d%H%M%S)"

# AWS Configuration - get from environment or use defaults
AWS_REGION="${AWS_REGION:-eu-west-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-}"  # Must be provided by user

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

            # Extract variable name and value
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

# Check required environment variables
check_env_vars() {
    print_message "Checking required environment variables..."

    # Check AWS deployment variables (not from .env file)
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        print_error "AWS_ACCOUNT_ID environment variable is required"
        print_message "Set it with: export AWS_ACCOUNT_ID=your-account-id"
        print_message "Or add it to your shell profile"
        exit 1
    fi

    # Check application variables (from .env file)
    local app_required_vars=(
        "API_TOKEN"
        "WTL_API_URL"
        "WTL_API_TOKEN"
    )

    local missing_vars=()

    for var in "${app_required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -gt 0 ]; then
        print_error "Missing required application variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo ""
        print_message "Add these variables to your .env file"
        exit 1
    fi

    print_success "All required environment variables are set"
    print_message "AWS_REGION: $AWS_REGION (deployment)"
    print_message "AWS_ACCOUNT_ID: $AWS_ACCOUNT_ID (deployment)"
}

# Check required tools
check_tools() {
    print_message "Checking required tools..."

    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed"
        print_message "Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        exit 1
    fi

    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        print_message "Install: https://docs.docker.com/get-docker/"
        exit 1
    fi

    print_success "Required tools are available"
}

# Check AWS authentication
check_aws_auth() {
    print_message "Checking AWS authentication..."

    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS authentication failed"
        print_message "Run: aws configure"
        exit 1
    fi

    local account_id=$(aws sts get-caller-identity --query Account --output text)
    if [ "$account_id" != "$AWS_ACCOUNT_ID" ]; then
        print_warning "Current AWS account ($account_id) differs from configured account ($AWS_ACCOUNT_ID)"
    fi

    print_success "AWS authentication successful"
}

# Create ECR repository if it doesn't exist
create_ecr_repository() {
    local repo_uri="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_REPOSITORY}"

    print_message "Creating ECR repository if needed..." >&2

    if ! aws ecr describe-repositories --repository-names "$IMAGE_REPOSITORY" --region "$AWS_REGION" &> /dev/null; then
        print_message "Creating ECR repository: $IMAGE_REPOSITORY" >&2
        aws ecr create-repository \
            --repository-name "$IMAGE_REPOSITORY" \
            --region "$AWS_REGION" \
            --image-scanning-configuration scanOnPush=true \
            --encryption-configuration encryptionType=AES256 > /dev/null
        print_success "ECR repository created" >&2
    else
        print_message "ECR repository already exists" >&2
    fi

    echo "$repo_uri"
}

# Build and push Docker image to ECR
build_and_push_image() {
    local repo_uri="$1"
    print_message "Building and pushing Docker image..."

    # Extract just the registry hostname (without repository name) for Docker login
    local registry_host="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

    # Get login token for ECR
    print_message "Authenticating Docker to ECR..."
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$registry_host"

    # Build image with unique tag
    print_message "Building Docker image with tag: $IMAGE_TAG ..."
    cd "$(dirname "$0")/.."
    docker build -t "$IMAGE_REPOSITORY:$IMAGE_TAG" .

    # Tag for ECR
    docker tag "$IMAGE_REPOSITORY:$IMAGE_TAG" "$repo_uri:$IMAGE_TAG"

    # Push to ECR
    print_message "Pushing image to ECR..."
    docker push "$repo_uri:$IMAGE_TAG"

    print_success "Image pushed to ECR: $repo_uri:$IMAGE_TAG"
}

# Create IAM role for App Runner ECR access
create_apprunner_access_role() {
    print_message "Creating IAM role for App Runner ECR access..." >&2

    local role_name="AppRunnerECRAccessRole"
    local policy_arn="arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"

    # Check if role already exists
    if aws iam get-role --role-name "$role_name" &> /dev/null; then
        print_message "IAM role already exists" >&2
    else
        print_message "Creating IAM role: $role_name" >&2

        # Trust policy for App Runner
        local trust_policy='{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "build.apprunner.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }'

        # Create role
        aws iam create-role \
            --role-name "$role_name" \
            --assume-role-policy-document "$trust_policy" \
            --description "Role for App Runner to access ECR" > /dev/null

        # Attach policy
        aws iam attach-role-policy \
            --role-name "$role_name" \
            --policy-arn "$policy_arn"

        print_success "IAM role created and policy attached" >&2

        # Wait a bit for role to propagate
        sleep 5
    fi

    local role_arn="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${role_name}"
    echo "$role_arn"
}

# Create App Runner service configuration
create_apprunner_config() {
    local repo_uri="$1"
    local access_role_arn="$2"

    cat > "/tmp/apprunner-config.json" << EOF
{
  "ServiceName": "${SERVICE_NAME}",
  "SourceConfiguration": {
    "ImageRepository": {
      "ImageIdentifier": "${repo_uri}:${IMAGE_TAG}",
      "ImageConfiguration": {
        "Port": "${CONTAINER_PORT}",
        "RuntimeEnvironmentVariables": {
          "APP_NAME": "wtl-hlr-hss-connector",
          "LOG_LEVEL": "${LOG_LEVEL:-INFO}",
          "DEBUG": "${DEBUG:-false}",
          "API_TOKEN": "${API_TOKEN}",
          "WTL_API_URL": "${WTL_API_URL}",
          "WTL_API_TOKEN": "${WTL_API_TOKEN}",
          "WTL_DEFAULT_CS_PROFILE": "${WTL_DEFAULT_CS_PROFILE:-default}",
          "WTL_DEFAULT_EPS_PROFILE": "${WTL_DEFAULT_EPS_PROFILE:-default}",
          "WTL_HTTP_REQUESTS_TIMEOUT": "${WTL_HTTP_REQUESTS_TIMEOUT:-30.0}",
          "WTL_IMSI_REGEXP": "${WTL_IMSI_REGEXP:-}"
        }
      },
      "ImageRepositoryType": "ECR"
    },
    "AuthenticationConfiguration": {
      "AccessRoleArn": "${access_role_arn}"
    },
    "AutoDeploymentsEnabled": false
  },
  "InstanceConfiguration": {
    "Cpu": "${CPU}",
    "Memory": "${MEMORY}"
  },
  "AutoScalingConfigurationArn": ""
}
EOF
}

# Create Auto Scaling configuration
create_autoscaling_config() {
    print_message "Creating Auto Scaling configuration..." >&2

    # If MIN_SIZE is 0, don't create custom autoscaling - use App Runner default scale-to-zero
    if [ "$MIN_SIZE" = "0" ]; then
        print_message "MIN_SIZE=0 detected - using App Runner default scale-to-zero behavior" >&2
        print_success "Default autoscaling will be used (supports scale-to-zero)" >&2
        echo ""
        return
    fi

    local config_name="wtl-hlr-hss-autoscaling"  # Shortened to fit 32 char limit

    # Check if auto scaling config already exists
    if aws apprunner list-auto-scaling-configurations \
        --region "$AWS_REGION" \
        --query "AutoScalingConfigurationSummaryList[?AutoScalingConfigurationName=='$config_name'].AutoScalingConfigurationArn" \
        --output text | grep -q .; then
        print_message "Auto Scaling configuration already exists" >&2
        local autoscaling_arn=$(aws apprunner list-auto-scaling-configurations \
            --region "$AWS_REGION" \
            --query "AutoScalingConfigurationSummaryList[?AutoScalingConfigurationName=='$config_name'].AutoScalingConfigurationArn" \
            --output text)
    else
        print_message "Creating new Auto Scaling configuration..." >&2
        local autoscaling_arn=$(aws apprunner create-auto-scaling-configuration \
            --auto-scaling-configuration-name "$config_name" \
            --min-size "$MIN_SIZE" \
            --max-size "$MAX_SIZE" \
            --max-concurrency "$MAX_CONCURRENCY" \
            --region "$AWS_REGION" \
            --query "AutoScalingConfiguration.AutoScalingConfigurationArn" \
            --output text 2>/dev/null)

        if [ -n "$autoscaling_arn" ] && [ "$autoscaling_arn" != "None" ]; then
            print_success "Auto Scaling configuration created" >&2
        else
            print_error "Failed to create Auto Scaling configuration" >&2
            print_warning "Continuing without custom autoscaling..." >&2
            autoscaling_arn=""
        fi
    fi

    echo "$autoscaling_arn"
}

# Deploy or update App Runner service
deploy_apprunner_service() {
    local repo_uri="$1"
    local autoscaling_arn="$2"

    print_message "Deploying App Runner service..."

    # Create access role
    local access_role_arn=$(create_apprunner_access_role)

    # Create config file with auto scaling ARN
    create_apprunner_config "$repo_uri" "$access_role_arn"

    # Update the config with auto scaling ARN (only if not empty)
    if [ -n "$autoscaling_arn" ]; then
        jq --arg arn "$autoscaling_arn" \
           '.AutoScalingConfigurationArn = $arn' \
           /tmp/apprunner-config.json > /tmp/apprunner-config-final.json
    else
        # Remove the AutoScalingConfigurationArn field if empty
        jq 'del(.AutoScalingConfigurationArn)' /tmp/apprunner-config.json > /tmp/apprunner-config-final.json
    fi

    # Check if service exists
    if aws apprunner describe-service \
        --service-arn "arn:aws:apprunner:${AWS_REGION}:${AWS_ACCOUNT_ID}:service/${SERVICE_NAME}" \
        --region "$AWS_REGION" &> /dev/null; then
        print_message "Updating existing App Runner service..."

        # Create separate config files for update
        jq '.SourceConfiguration' /tmp/apprunner-config-final.json > /tmp/source-config.json
        jq '.InstanceConfiguration' /tmp/apprunner-config-final.json > /tmp/instance-config.json

        # Update service with file references
        local update_cmd="aws apprunner update-service \
            --service-arn \"arn:aws:apprunner:${AWS_REGION}:${AWS_ACCOUNT_ID}:service/${SERVICE_NAME}\" \
            --source-configuration file:///tmp/source-config.json \
            --instance-configuration file:///tmp/instance-config.json \
            --region \"$AWS_REGION\""

        # Only add autoscaling if ARN is provided
        if [ -n "$autoscaling_arn" ]; then
            update_cmd="$update_cmd --auto-scaling-configuration-arn \"$autoscaling_arn\""
        fi

        eval "$update_cmd"
        print_success "App Runner service update initiated"
    else
        print_message "Creating new App Runner service..."

        aws apprunner create-service \
            --cli-input-json file:///tmp/apprunner-config-final.json \
            --region "$AWS_REGION"

        print_success "App Runner service creation initiated"
    fi

    # Clean up temp files
    rm -f /tmp/apprunner-config.json \
          /tmp/apprunner-config-final.json \
          /tmp/source-config.json \
          /tmp/instance-config.json
}

# Wait for service to be ready
wait_for_service() {
    print_message "Waiting for service to be ready..."

    local service_arn="arn:aws:apprunner:${AWS_REGION}:${AWS_ACCOUNT_ID}:service/${SERVICE_NAME}"
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        local status=$(aws apprunner describe-service \
            --service-arn "$service_arn" \
            --region "$AWS_REGION" \
            --query "Service.Status" \
            --output text)

        case "$status" in
            "RUNNING")
                print_success "Service is running!"
                return 0
                ;;
            "CREATE_FAILED"|"UPDATE_FAILED"|"DELETE_FAILED")
                print_error "Service deployment failed with status: $status"
                return 1
                ;;
            *)
                print_message "Service status: $status (attempt $attempt/$max_attempts)"
                sleep 30
                ;;
        esac

        ((attempt++))
    done

    print_error "Service did not become ready within expected time"
    return 1
}

# Get service URL
get_service_url() {
    print_message "Getting service URL..." >&2

    local service_arn="arn:aws:apprunner:${AWS_REGION}:${AWS_ACCOUNT_ID}:service/${SERVICE_NAME}"
    local service_url=$(aws apprunner describe-service \
        --service-arn "$service_arn" \
        --region "$AWS_REGION" \
        --query "Service.ServiceUrl" \
        --output text)

    echo "https://$service_url"
}

# Test the deployed service
test_service() {
    local service_url="$1"

    print_message "Testing deployed service..."

    # Test health endpoint
    print_message "Testing health endpoint..."
    if curl -f -s "$service_url/health" > /dev/null; then
        print_success "Health check passed"
    else
        print_warning "Health check failed - service may still be starting"
    fi

    # Test API endpoint (requires auth)
    print_message "Testing authenticated endpoint..."
    local test_payload='{
        "event_id": "test-12345",
        "data": {
            "account": {"i_account": 12345},
            "event_type": "account_bill_status_changed",
            "sim_info": {"imsi": "901700000050170"},
            "bill_status": "O",
            "blocked_status": "N"
        }
    }'

    local response_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$service_url/process-event" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $API_TOKEN" \
        -d "$test_payload")

    case "$response_code" in
        "202")
            print_success "API test passed - service is working correctly"
            ;;
        "401")
            print_warning "API test returned 401 - check API_TOKEN configuration"
            ;;
        "422")
            print_warning "API test returned 422 - check WTL configuration or test payload"
            ;;
        *)
            print_warning "API test returned unexpected status: $response_code"
            ;;
    esac
}

# Show service information
show_service_info() {
    local service_url="$1"

    echo ""
    echo "======================================"
    print_success "Deployment completed successfully!"
    echo "======================================"
    print_message "Service Name: $SERVICE_NAME"
    print_message "Region: $AWS_REGION"
    print_message "Service URL: $service_url"
    print_message "Health Check: $service_url/health"
    print_message "API Endpoint: $service_url/process-event"
    echo ""
    print_message "You can monitor the service in AWS Console:"
    print_message "https://console.aws.amazon.com/apprunner/home?region=${AWS_REGION}#/services"
    echo ""
    echo "To test the API:"
    echo "curl -X POST \"$service_url/process-event\" \\"
    echo "  -H \"Content-Type: application/json\" \\"
    echo "  -H \"Authorization: Bearer \$API_TOKEN\" \\"
    echo "  -d '{...}'"
}

# Main deployment function
main() {
    echo "======================================"
    echo " WTL HLR/HSS Connector AWS App Runner Deployment"
    echo "======================================"

    load_env_file
    check_env_vars
    check_tools
    check_aws_auth

    # Create ECR repository and get URI
    local repo_uri=$(create_ecr_repository)

    # Build and push image
    build_and_push_image "$repo_uri"

    # Create auto scaling configuration
    local autoscaling_arn=$(create_autoscaling_config)

    # Deploy service
    deploy_apprunner_service "$repo_uri" "$autoscaling_arn"

    # Wait for service to be ready
    if wait_for_service; then
        local service_url=$(get_service_url)
        test_service "$service_url"
        show_service_info "$service_url"
    else
        print_error "Deployment failed"
        exit 1
    fi
}

# Show usage
usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help    Show this help message"
    echo "  --test-only   Only test the existing service"
    echo "  --destroy     Delete the App Runner service"
    echo ""
    echo "Required environment variables:"
    echo "  AWS_REGION        - AWS Region (e.g., 'eu-west-1')"
    echo "  AWS_ACCOUNT_ID    - AWS Account ID (e.g., '123456789012')"
    echo "  API_TOKEN         - Bearer token for API authentication"
    echo "  WTL_API_URL       - WTL API base URL"
    echo "  WTL_API_TOKEN     - WTL API authentication token"
    echo ""
    echo "Optional environment variables:"
    echo "  LOG_LEVEL                  - Log level (default: INFO)"
    echo "  DEBUG                      - Debug mode (default: false)"
    echo "  WTL_DEFAULT_CS_PROFILE     - Default CS profile (default: default)"
    echo "  WTL_DEFAULT_EPS_PROFILE    - Default EPS profile (default: default)"
    echo "  WTL_HTTP_REQUESTS_TIMEOUT  - HTTP timeout (default: 30.0)"
    echo "  WTL_IMSI_REGEXP           - IMSI validation regex (optional)"
    echo ""
    echo "Example:"
    echo "  export AWS_REGION='eu-west-1'"
    echo "  export AWS_ACCOUNT_ID='123456789012'"
    echo "  export API_TOKEN='your-secure-token'"
    echo "  export WTL_API_URL='https://wtl-api.example.com/wtl/hlr/v1'"
    echo "  export WTL_API_TOKEN='your-wtl-token'"
    echo "  $0"
}

# Test existing service
test_only() {
    load_env_file
    check_env_vars

    local service_url=$(get_service_url)
    if [ -n "$service_url" ]; then
        test_service "$service_url"
        show_service_info "$service_url"
    else
        print_error "Service not found or not running"
        exit 1
    fi
}

# Destroy service
destroy_service() {
    print_warning "This will DELETE the App Runner service and all its data!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_message "Operation cancelled"
        exit 0
    fi

    load_env_file
    check_env_vars
    check_aws_auth

    local service_arn="arn:aws:apprunner:${AWS_REGION}:${AWS_ACCOUNT_ID}:service/${SERVICE_NAME}"

    print_message "Deleting App Runner service..."
    aws apprunner delete-service \
        --service-arn "$service_arn" \
        --region "$AWS_REGION"

    print_success "Service deletion initiated"
    print_message "You can monitor the deletion in AWS Console"
}

# Parse command line arguments
case "$1" in
    "-h"|"--help")
        usage
        exit 0
        ;;
    "--test-only")
        test_only
        exit 0
        ;;
    "--destroy")
        destroy_service
        exit 0
        ;;
    "")
        main "$@"
        ;;
    *)
        print_error "Unknown option: $1"
        usage
        exit 1
        ;;
esac