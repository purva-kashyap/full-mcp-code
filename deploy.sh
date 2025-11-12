#!/bin/bash
# Deployment script for MCP Server and Web App to Kubernetes

set -e

echo "🚀 Deploying MCP Server and Web App to Kubernetes"
echo "=================================================="

# Configuration
NAMESPACE="mcp-system"
MCP_SERVER_IMAGE="${MCP_SERVER_IMAGE:-mcp-server:latest}"
MCP_WEB_APP_IMAGE="${MCP_WEB_APP_IMAGE:-mcp-web-app:latest}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}📦 Step 1: Building Docker images${NC}"
echo "Building mcp-server..."
cd mcp-server
docker build -t $MCP_SERVER_IMAGE .
cd ..

echo "Building mcp-web-app..."
cd mcp-web-app
docker build -t $MCP_WEB_APP_IMAGE .
cd ..

echo -e "${GREEN}✅ Docker images built successfully${NC}"

echo -e "${YELLOW}🔐 Step 2: Create Kubernetes secrets${NC}"
echo "Please ensure you've updated k8s/secret.yaml with your Azure credentials"
read -p "Press enter to continue..."

echo -e "${YELLOW}📝 Step 3: Applying Kubernetes manifests${NC}"

# Create namespace
echo "Creating namespace..."
kubectl apply -f mcp-server/k8s/namespace.yaml

# Deploy MCP Server
echo "Deploying MCP Server..."
kubectl apply -f mcp-server/k8s/secret.yaml
kubectl apply -f mcp-server/k8s/configmap.yaml
kubectl apply -f mcp-server/k8s/pvc.yaml
kubectl apply -f mcp-server/k8s/deployment.yaml
kubectl apply -f mcp-server/k8s/ingress.yaml

# Deploy MCP Web App
echo "Deploying MCP Web App..."
kubectl apply -f mcp-web-app/k8s/configmap.yaml
kubectl apply -f mcp-web-app/k8s/deployment.yaml
kubectl apply -f mcp-web-app/k8s/ingress.yaml

echo -e "${GREEN}✅ Kubernetes manifests applied${NC}"

echo -e "${YELLOW}⏳ Step 4: Waiting for deployments to be ready${NC}"
kubectl wait --for=condition=available --timeout=300s \
  deployment/mcp-server -n $NAMESPACE

kubectl wait --for=condition=available --timeout=300s \
  deployment/mcp-web-app -n $NAMESPACE

echo -e "${GREEN}✅ All deployments are ready!${NC}"

echo ""
echo "🎉 Deployment Complete!"
echo "======================="
echo ""
echo "Services:"
echo "  MCP Server FastAPI:  http://mcp-server.$NAMESPACE.svc.cluster.local:8000"
echo "  MCP Server MCP:      http://mcp-server.$NAMESPACE.svc.cluster.local:8001"
echo "  MCP Web App:         http://mcp-web-app.$NAMESPACE.svc.cluster.local"
echo ""
echo "To check status:"
echo "  kubectl get pods -n $NAMESPACE"
echo "  kubectl get svc -n $NAMESPACE"
echo "  kubectl get ingress -n $NAMESPACE"
echo ""
echo "To view logs:"
echo "  kubectl logs -f deployment/mcp-server -n $NAMESPACE"
echo "  kubectl logs -f deployment/mcp-web-app -n $NAMESPACE"
