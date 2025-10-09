.PHONY: help build run stop logs clean health dev gcp-deploy gcp-deploy-force gcp-update-env gcp-logs gcp-status aws-deploy aws-deploy-force aws-update-env aws-logs aws-status aws-destroy aws-test-only

# Read REGION from .env file if it exists
REGION ?= $(shell grep '^REGION=' .env 2>/dev/null | cut -d'=' -f2 || echo "europe-west3")
AWS_REGION ?= $(shell grep '^AWS_REGION=' .env 2>/dev/null | cut -d'=' -f2 || echo "eu-west-1")

# Default target
help:
	@echo "🔧 WTL HLR/HSS Connector - Available Commands"
	@echo "=============================================="
	@echo ""
	@echo "Local Development:"
	@echo "  build          - Build the Docker image"
	@echo "  run            - Run the service with docker compose"
	@echo "  stop           - Stop the service"
	@echo "  logs           - Show service logs"
	@echo "  clean          - Clean up project Docker resources"
	@echo "  health         - Check service health"
	@echo "  dev            - Run in development mode"
	@echo ""
	@echo "Google Cloud Platform - Cloud Run:"
	@echo "  gcp-deploy        - Deploy to Cloud Run (interactive)"
	@echo "  gcp-deploy-force  - Force full redeploy"
	@echo "  gcp-update-env    - Update environment variables only"
	@echo "  gcp-logs          - View service logs"
	@echo "  gcp-status        - Check service status"
	@echo ""
	@echo "Amazon Web Services - App Runner:"
	@echo "  aws-deploy        - Deploy to App Runner (interactive)"
	@echo "  aws-deploy-force  - Force full redeploy"
	@echo "  aws-update-env    - Update environment variables only"
	@echo "  aws-logs          - View service logs"
	@echo "  aws-status        - Check service status"
	@echo "  aws-test-only     - Test existing App Runner service only"
	@echo "  aws-destroy       - Delete App Runner service"

# ====== Local Development ======

# Build Docker image
build:
	docker compose build

# Run the service
run:
	docker compose up -d

# Stop the service
stop:
	docker compose down

# Show logs
logs:
	docker compose logs -f wtl-hlr-hss-connector

# Clean up project resources only (safe)
clean:
	docker compose down --volumes --remove-orphans
	docker compose rm -f
	docker image rm -f wtl-hlr-hss-microservice-wtl-hlr-hss-connector 2>/dev/null || true

# Check service health
health:
	@echo "Checking service health..."
	curl -f http://localhost:8000/health || echo "Service is not healthy"

# Development mode (local)
dev:
	@echo "Starting development server..."
	@echo "Make sure to set environment variables first!"
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# ====== Google Cloud Platform - Cloud Run ======

gcp-deploy:
	@echo "🚀 Deploying to Google Cloud Run..."
	./_gcp-deploy/deploy_cloud_run_service.sh

gcp-deploy-force:
	@echo "🚀 Force deploying to Google Cloud Run..."
	./_gcp-deploy/deploy_cloud_run_service.sh --force-deploy

gcp-update-env:
	@echo "🔧 Updating environment variables..."
	./_gcp-deploy/deploy_cloud_run_service.sh --env-only

gcp-logs:
	@echo "📋 Viewing Cloud Run logs..."
	gcloud run services logs read wtl-hlr-hss-connector --region=$(REGION) --limit=50

gcp-status:
	@echo "📊 Checking Cloud Run service status..."
	gcloud run services describe wtl-hlr-hss-connector --region=$(REGION)

# ====== Amazon Web Services - App Runner ======

aws-deploy:
	@echo "🚀 Deploying to AWS App Runner..."
	./_aws-deploy/deploy_apprunner.sh

aws-deploy-force:
	@echo "🚀 Force deploying to AWS App Runner..."
	./_aws-deploy/deploy_apprunner.sh --force-deploy

aws-update-env:
	@echo "🔧 Updating environment variables..."
	./_aws-deploy/deploy_apprunner.sh --env-only

aws-logs:
	@echo "📋 Viewing App Runner logs..."
	aws logs get-log-events --log-group-name /aws/apprunner/wtl-hlr-hss-connector --log-stream-name latest --region=$(AWS_REGION) --limit=50

aws-status:
	@echo "📊 Checking App Runner service status..."
	aws apprunner describe-service --service-name wtl-hlr-hss-connector --region=$(AWS_REGION)

aws-test-only:
	@echo "🧪 Testing existing AWS App Runner service only..."
	./_aws-deploy/deploy_apprunner.sh --test-only

aws-destroy:
	@echo "🗑️  Deleting App Runner service..."
	./_aws-deploy/deploy_apprunner.sh --destroy