# FinOps AI Agent

[![Python](https://img.shields.io/badge/Python-50.9%25-blue?style=flat-square)](.)
[![TypeScript](https://img.shields.io/badge/TypeScript-46.5%25-2d72b8?style=flat-square)](.)
[![CSS](https://img.shields.io/badge/CSS-2.4%25-563d7c?style=flat-square)](.)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0+-009688?style=flat-square)](.)
[![LangSmith](https://img.shields.io/badge/LangSmith-Integrated-2d72b8?style=flat-square)](https://smith.langchain.com)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Production-326ce5?style=flat-square)](.)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)]()

> **Intelligent AI-powered platform for Azure cloud cost optimization with enterprise-grade monitoring, comprehensive agent workflow tracing, automated recommendation evaluation, and production-ready Kubernetes deployment on Proxmox infrastructure.**

---

## 🎯 Executive Summary

**FinOps AI Agent** is a production-ready cloud cost optimization platform that leverages advanced AI reasoning to identify inefficiencies in Azure infrastructure and execute cost-saving actions with human oversight. Built for enterprise teams, it combines intelligent analysis with actionable automation to reduce unnecessary cloud spending while maintaining security and compliance.

Deployed on a **resilient 3-node Kubernetes cluster** (Proxmox-based infrastructure) with automated CI/CD pipelines, rolling update strategies, and production-grade load balancing via MetalLB.

### The Problem
Organizations are overspending on cloud infrastructure by **20-30%** due to:
- Overprovisioned resources running at low utilization
- Idle or forgotten resources consuming costs
- Suboptimal configurations and poor cost allocation
- Lack of visibility into spending patterns and anomalies
- Manual, time-consuming optimization processes

### The Solution
**FinOps AI Agent** automates cloud cost optimization through:
- 🤖 **Intelligent Analysis** - AI-powered detection of inefficiencies and cost-saving opportunities
- 📊 **Real-Time Visibility** - Comprehensive dashboards showing costs, metrics, and resource utilization
- ⚡ **Approved Automation** - Execute optimizations directly on Azure with proper controls and audit trails
- 🛡️ **Enterprise Monitoring** - LangSmith integration for full LLM reliability, performance tracking, and recommendation accuracy
- 🚀 **Production Infrastructure** - Kubernetes-based deployment with high availability and automated updates

### Key Impact
- **Reduce cloud spending** by 15-30% through intelligent optimization
- **Decrease manual work** with automated detection and execution
- **Maintain control** with approval workflows and comprehensive audit logs
- **Ensure reliability** with LLM monitoring and continuous evaluation
- **Enterprise-Grade Deployment** - Resilient, scalable, and self-healing infrastructure

---

## 🚀 Platform Highlights

### For Finance & Operations Teams
- **Cost Visibility Dashboard** - Track Azure spending with real-time metrics and trend analysis
- **Automated Savings Identification** - AI discovers $10K-$100K+ monthly savings opportunities
- **Approval Workflows** - Built-in controls ensure only authorized optimizations execute
- **Audit & Compliance** - Complete action history and reasoning for finance audits
- **ROI Tracking** - Measure impact of implemented optimizations

### For Engineering & DevOps Teams
- **Intelligent Recommendations** - Context-aware suggestions based on workload patterns
- **Safe Execution** - All actions require explicit approval; no automatic mass deletion
- **Detailed Tracing** - Complete visibility into why recommendations were made
- **Performance Monitoring** - Track LLM efficiency and recommendation accuracy
- **Easy Integration** - REST APIs and modern Python/TypeScript stack
- **Production Kubernetes** - Deploy with confidence on Proxmox infrastructure
- **Automated CI/CD** - GitHub Actions workflows for seamless deployment

### For Executive Leadership
- **Strategic Cost Reduction** - Move beyond reporting to actionable optimization
- **Competitive Advantage** - Reduce cloud spending, improve margins, scale faster
- **Risk Mitigation** - Enterprise-grade controls, audit trails, and security
- **Data-Driven Decisions** - Powered by AI analysis of your actual infrastructure
- **Scalable Solution** - Handles multi-team, multi-subscription Azure environments
- **High Availability** - 99.9% uptime with redundant infrastructure

---

## 💡 How It Works

```
┌─────────────────────────────────────────────────────────────┐
│            FINOPS AI AGENT WORKFLOW                          │
└─────────────────────────────────────────────────────────────┘

1️⃣ OBSERVE
   ↓
   Analyze Azure infrastructure in real-time
   • Resource inventory (VMs, databases, storage, networks)
   • Cost Management APIs for spending patterns
   • Performance metrics and utilization data
   • Security and compliance status

2️⃣ ANALYZE  
   ↓
   Apply AI reasoning to identify optimization opportunities
   • Detect overprovisioned resources
   • Find unused or idle infrastructure
   • Spot cost anomalies and inefficient configurations
   • Calculate potential savings for each opportunity

3️⃣ RECOMMEND
   ↓
   Generate prioritized, actionable recommendations
   • Resize underutilized VMs
   • Remove unused resources
   • Optimize storage tiers
   • Recommend reserved instances
   • Each with confidence scores and estimated savings

4️⃣ APPROVE
   ↓
   Human review and controlled execution
   • Dashboard shows recommendations for review
   • Teams approve specific actions
   • AI validates prerequisites and dependencies
   • Actions execute with full audit logging

5️⃣ MONITOR
   ↓
   Track results and improve continuously
   • Measure actual cost savings
   • Monitor LLM performance and accuracy
   • Evaluate recommendation correctness
   • Continuous learning and optimization
```

---

## 📊 Platform Capabilities

### ✨ Intelligent Cost Analysis
- **Azure Resource Discovery** - Real-time inventory of all resources, costs, and utilization
- **Anomaly Detection** - Identify unexpected spending spikes and inefficiencies
- **Pattern Recognition** - Learn workload patterns to make context-aware suggestions
- **Cost Trend Analysis** - Forecast future spending and identify optimization windows
- **Savings Calculation** - Estimate exact cost impact of each optimization

### ⚡ Approved Automation
- **Safe Execution** - All resource-modifying actions require explicit approval
- **Intelligent Validation** - Verify prerequisites and dependencies before execution
- **Rollback Capability** - Track all changes for audit and potential reversal
- **Granular Controls** - Set policies on what optimizations are allowed per team
- **Complete Audit Trail** - Every action logged with reasoning and results

### 📈 Comprehensive Visibility
- **Real-Time Dashboard** - Cost breakdowns, resource metrics, and optimization status
- **Executive Reports** - Summary metrics for leadership and board presentations
- **Detailed Analytics** - Deep dives into resource utilization and cost drivers
- **Trends & Forecasting** - Historical data and predictive spending models
- **Custom Views** - Role-based dashboards for finance, engineering, and executive teams

### 🛡️ Enterprise Security
- **Role-Based Access Control** - Granular permissions for different teams and roles
- **JWT Authentication** - Secure API endpoints with token management
- **Encrypted Credentials** - Secure storage and handling of Azure credentials
- **Audit Logging** - Complete record of all actions for compliance and investigation
- **TLS/HTTPS** - All communications encrypted in production

### 🔍 LLM Monitoring & Evaluation
- **Agent Workflow Tracing** - Complete visibility into LangGraph execution and decisions
- **Performance Tracking** - Monitor latency, token usage, and LLM costs
- **Automated Evaluation** - Test recommendations against expected outcomes
- **Accuracy Metrics** - Track precision, recall, and false positive rates
- **Continuous Improvement** - Learn from successes and failures to improve future recommendations

---

## 🎯 Core Capabilities

### 1. **Intelligent Cost Analysis**
- Analyze Azure resource usage and spending patterns
- Detect inefficiencies, anomalies, and overprovisioned resources
- Identify unused or underutilized resources
- Trend analysis for proactive cost management

### 2. **Azure Integration**
- Real-time resource inventory from Azure
- Cost Management APIs for detailed billing analysis
- Monitor integration for performance metrics
- Security and Policy Insights for compliance-aware optimization
- Deep visibility into compute, storage, networking, and database resources

### 3. **AI-Driven Recommendations**
- AI reasoning workflows powered by LangGraph
- Context-aware optimization suggestions
- Prioritized recommendations based on potential savings
- Reasoning transparency for auditability

### 4. **Approved Automation & Execution**
- Execute cost-saving actions directly on Azure resources
- Resize underutilized virtual machines
- Remove unused resources (disks, network interfaces, etc.)
- Modify resource configurations for optimization
- All actions require explicit approval through the dashboard
- Comprehensive audit logs for compliance and accountability

### 5. **Comprehensive Dashboard**
- Real-time cost visualization and trend analysis
- Resource utilization metrics and performance data
- Prioritized optimization opportunities
- Execution history and audit trails
- Role-based views for different stakeholder needs

### 6. **Authentication & Security**
- JWT-based authentication with token refresh
- Role-based access control (RBAC)
- Secure Azure credential management
- Encryption of sensitive data at rest and in transit

---

## 🛡️ LangSmith Integration - Most Valuable Features

### 🔍 Agent Workflow Tracing (High Priority)
**Visualize the execution of your LangGraph nodes with complete visibility:**

- **Azure Observation Node** - Track resource data collection, API calls, and data retrieval performance
- **Cost Analysis Node** - Monitor cost data aggregation, trend calculations, and anomaly detection
- **Security Analysis Node** - Trace security risk detection, compliance checks, and policy validation
- **Recommendation Generation Node** - Observe AI reasoning, LLM calls, cost/benefit analysis, and prioritization
- **Approval Node** - Monitor approval workflow, validation logic, and execution decisions

**Benefits:** Complete DAG visibility, per-node metrics, error tracking, performance optimization

### 📊 Performance & Cost Monitoring (High Priority)
**Track response latency, token consumption, LLM costs, and execution failures:**

- **Response Latency** - End-to-end tracking, per-node breakdown, bottleneck identification
- **Token Usage** - Input/output tracking, efficiency analysis, cost optimization
- **LLM Costs** - Real-time per-recommendation costs, ROI vs. savings achieved
- **Failure Tracking** - Error rates, retry patterns, root cause analysis

**Benefits:** Optimize efficiency, control costs, maintain SLAs, prevent failures

### ✅ Automated Evaluation (High Priority)
**Create test datasets with Azure scenarios and expected recommendations. Evaluate correctness:**

- **Test Dataset Management** - Realistic Azure scenarios with expected outcomes
- **Evaluation Framework** - Automated comparison against expected results
- **Continuous Evaluation** - Run on every deployment, track trends
- **Accuracy Metrics** - Precision, recall, false positive/negative detection

**Benefits:** Ensure recommendation quality, detect degradation, continuous improvement

---

## 🏗️ Production Infrastructure & Deployment

### Proxmox Cluster Architecture (High Availability)

**3-Node Kubernetes Cluster Setup:**

```
┌─────────────────────────────────────────────────────────────┐
│                    PROXMOX CLUSTER                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Kubernetes  │  │  Kubernetes  │  │  QDevice     │      │
│  │   Master     │  │   Worker     │  │  (Quorum)    │      │
│  │   Node 1     │  │   Node 2     │  │   Node 3     │      │
│  │              │  │              │  │              │      │
│  │ • Control    │  │ • Workloads  │  │ • Quorum     │      │
│  │ • API Server │  │ • Kubelet    │  │ • Witness    │      │
│  │ • Scheduler  │  │ • CRI-O      │  │ • HA Manager │      │
│  │ • etcd       │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│                   ┌────────▼────────┐                       │
│                   │  MetalLB         │                       │
│                   │  Load Balancer   │                       │
│                   │  (L4 + L7)       │                       │
│                   └─────────┬────────┘                       │
│                             │                                │
│                   ┌─────────▼────────┐                      │
│                   │  Ingress NGINX   │                      │
│                   │  (L7 Routing)    │                      │
│                   └────────┬─────────┘                      │
│                            │                                 │
└─────────────────────────────┼─────────────────────────────────┘
                              │
                    ┌─────────▼────────┐
                    │   Services       │
                    │ ├─ API Backend   │
                    │ ├─ Frontend      │
                    │ ├─ Database      │
                    │ └─ Monitoring    │
                    └──────────────────┘
```

### Kubernetes Configuration

**Rolling Update Strategy:**
```yaml
# Deployment Strategy for Zero-Downtime Updates
- Type: RollingUpdate
- MaxSurge: 1 (one additional pod during update)
- MaxUnavailable: 0 (no pods down during update)
- ProgressDeadlineSeconds: 600
- Automatic rollback on failure
```

**Key Infrastructure Components:**

1. **High Availability (HA)**
   - 3-node cluster with master + 2 workers
   - QDevice node for split-brain prevention
   - Automatic failover and recovery
   - Persistent volume replication

2. **Load Balancing**
   - **MetalLB** - Bare-metal load balancer (Layer 4 + Layer 7)
   - Automatic IP assignment from reserved pool
   - Health checks and automatic failover
   - Support for both TCP and UDP services

3. **Ingress & Routing**
   - **NGINX Ingress Controller** - Advanced L7 routing
   - TLS/SSL termination
   - URL path-based routing
   - Rate limiting and DDoS protection

4. **Storage**
   - Persistent Volumes (PV) for databases
   - Local storage optimization
   - Backup and disaster recovery
   - Automated snapshots

5. **Monitoring & Logging**
   - Prometheus for metrics collection
   - Grafana for visualization
   - ELK stack for log aggregation
   - Real-time alerting

---

## 🚀 Deployment & CI/CD Pipeline

### GitHub Actions Automated Workflow

**Complete CI/CD Pipeline:**

```yaml
Trigger: Push to main branch
         ↓
    1️⃣ BUILD STAGE (5 min)
       ├─ Lint & Test Backend (Python)
       ├─ Lint & Test Frontend (TypeScript)
       ├─ Build Docker images
       └─ Push to container registry
         ↓
    2️⃣ STAGING DEPLOYMENT (3 min)
       ├─ Deploy to staging cluster
       ├─ Run integration tests
       ├─ Run security scans
       └─ Performance testing
         ↓
    3️⃣ APPROVAL (manual gate)
         ↓
    4️⃣ PRODUCTION DEPLOYMENT (5 min)
       ├─ Rolling update (no downtime)
       ├─ Health checks
       ├─ Smoke tests
       └─ Notification to team
         ↓
    5️⃣ POST-DEPLOYMENT (ongoing)
       ├─ Monitor metrics
       ├─ Alert on anomalies
       └─ Auto-rollback on critical errors
```

### GitHub Actions Workflow Files

**.github/workflows/ci-cd.yml**
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      # Backend Testing
      - name: Test Backend
        run: |
          python -m pytest tests/
          python -m black --check app/
          python -m flake8 app/
      
      # Frontend Testing
      - name: Test Frontend
        run: |
          cd frontend
          npm install
          npm run lint
          npm run test
      
      # Build Docker Images
      - name: Build & Push Images
        run: |
          docker build -t finops-api:${{ github.sha }} -f Dockerfile.api .
          docker build -t finops-frontend:${{ github.sha }} -f Dockerfile.frontend .
          docker push ${{ secrets.REGISTRY }}/${{ secrets.IMAGE }}:${{ github.sha }}
      
      # Security Scanning
      - name: Security Scan
        run: |
          trivy image ${{ secrets.REGISTRY }}/finops-api:${{ github.sha }}
          trivy image ${{ secrets.REGISTRY }}/finops-frontend:${{ github.sha }}

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    steps:
      - name: Deploy to Staging
        run: |
          kubectl set image deployment/finops-api \
            api=${{ secrets.REGISTRY }}/finops-api:${{ github.sha }} \
            --namespace=staging
          kubectl rollout status deployment/finops-api -n staging

  deploy-production:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
    steps:
      - name: Deploy to Production
        run: |
          kubectl set image deployment/finops-api \
            api=${{ secrets.REGISTRY }}/finops-api:${{ github.sha }} \
            --namespace=production
          kubectl rollout status deployment/finops-api -n production
      
      - name: Smoke Tests
        run: |
          curl -f https://api.finopsai.com/health
          curl -f https://finopsai.com/
      
      - name: Notify Team
        uses: slack-notify@v1
        with:
          message: "Production deployment successful"
```

### Deployment Manifests

**Kubernetes Deployment Configuration:**

```yaml
# Deployment with Rolling Update Strategy
apiVersion: apps/v1
kind: Deployment
metadata:
  name: finops-api
  namespace: production
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: finops-api
  template:
    metadata:
      labels:
        app: finops-api
    spec:
      containers:
      - name: api
        image: finops-api:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# Service with MetalLB Load Balancer
apiVersion: v1
kind: Service
metadata:
  name: finops-api
  namespace: production
  annotations:
    metallb.universe.tf/address-pool: default
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
  selector:
    app: finops-api

---
# Ingress with NGINX Controller
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: finops-ingress
  namespace: production
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.finopsai.com
    - finopsai.com
    secretName: finops-tls
  rules:
  - host: api.finopsai.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: finops-api
            port:
              number: 80
  - host: finopsai.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: finops-frontend
            port:
              number: 80
```

### Quick Deployment Commands

```bash
# Deploy to Kubernetes cluster
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Monitor deployment
kubectl rollout status deployment/finops-api -n production
kubectl logs -f deployment/finops-api -n production

# Check cluster health
kubectl get nodes
kubectl get pods -n production
kubectl describe nodes

# Scale replicas
kubectl scale deployment/finops-api --replicas=5 -n production

# Perform rolling update
kubectl set image deployment/finops-api api=finops-api:v2.0 -n production
kubectl rollout status deployment/finops-api -n production

# Rollback if needed
kubectl rollout undo deployment/finops-api -n production
```

---

## 📁 Project Structure

```
finops-ai-agent/
├── api/                        # FastAPI endpoints
├── app/                        # Application logic
│   ├── agent/                 # LangGraph orchestration
│   ├── tools/                 # Azure & FinOps tools
│   ├── services/              # Business logic
│   └── database/              # Data persistence
├── frontend/                  # React dashboard
├── k8s/                       # Kubernetes manifests
│   ├── deployment.yaml        # API deployment config
│   ├── service.yaml           # Service definition
│   ├── ingress.yaml           # Ingress routing
│   ├── configmap.yaml         # Configuration
│   └── secrets.yaml           # Credentials
├── .github/workflows/         # CI/CD pipelines
│   └── ci-cd.yml             # GitHub Actions workflow
├── Dockerfile                 # Container image
├── docker-compose.yml         # Local development
├── migrations/                # Database migrations
├── main.py                    # Entry point
└── requirements.txt           # Dependencies
```

---

## 🛠️ Technology Stack

**Backend:** FastAPI • SQLAlchemy • LangChain/LangGraph • LangSmith • Azure SDK
**Frontend:** React 19 • TypeScript • Tailwind CSS v4 • TailAdmin
**Infrastructure:** 
- **Container:** Docker • CRI-O
- **Orchestration:** Kubernetes 1.27+
- **Load Balancing:** MetalLB • NGINX Ingress
- **Compute:** Proxmox VE (3-node cluster)
- **Storage:** Persistent Volumes • PostgreSQL
- **CI/CD:** GitHub Actions
- **Monitoring:** Prometheus • Grafana

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+, Node.js 18+, PostgreSQL 12+
- Kubernetes 1.27+ cluster (Proxmox-based or other)
- kubectl configured
- Azure Subscription with appropriate permissions
- OpenAI/Azure OpenAI API Key
- LangSmith API Key (optional, for monitoring)

### Local Development
```bash
# Clone and setup
git clone https://github.com/ghadamaalej/finops-ai-agent.git
cd finops-ai-agent

# Backend setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Configure credentials

# Frontend setup
cd frontend && npm install && cd ..

# Database
python -m app.database.init_db

# Run locally
python main.py  # Backend at http://localhost:8000
cd frontend && npm run dev  # Frontend at http://localhost:5173
```

### Kubernetes Deployment
```bash
# Deploy to cluster
kubectl apply -f k8s/

# Verify deployment
kubectl get all -n production

# Monitor logs
kubectl logs -f deployment/finops-api -n production

# Check ingress
kubectl get ingress -n production
```

See [INSTALLATION.md](INSTALLATION.md) for detailed setup and deployment guides.

---

## 📊 API Endpoints

**Agent Operations**
- `POST /api/agent/analyze` - Analyze costs and get recommendations
- `POST /api/agent/optimize` - Execute approved optimizations
- `GET /api/agent/recommendations` - Get pending recommendations
- `GET /api/agent/execution-history` - Action history and results

**Dashboard**
- `GET /api/dashboard/metrics` - KPIs and cost data
- `GET /api/dashboard/resources` - Resource inventory
- `GET /api/dashboard/agent-performance` - LangSmith metrics

**Monitoring**
- `GET /api/monitoring/langsmith/traces` - Workflow traces
- `GET /api/monitoring/evaluation-results` - Evaluation metrics

See [API Documentation](API.md) for complete endpoint reference.

---

## 🔐 Security & Compliance

- **Role-Based Access Control** - Granular permissions per team
- **Approval Workflows** - Human oversight on all resource changes
- **Complete Audit Trails** - Every action logged for compliance
- **Encrypted Credentials** - Secure credential storage and management
- **TLS/HTTPS** - Production encryption for all communications
- **Network Policies** - Kubernetes network segmentation
- **Pod Security** - Security context and RBAC policies
- **Secret Management** - Encrypted secrets in etcd
- **Image Scanning** - Trivy security scanning in CI/CD

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 📞 Get Started Today

### For Enterprises
**Schedule a demo:** [enterprise@finopsai.com](mailto:enterprise@finopsai.com)

### For Developers
**Clone and contribute:** [GitHub Repository](https://github.com/ghadamaalej/finops-ai-agent)

### Support
- 📖 [Documentation](https://docs.finopsai.com)
- 💬 [GitHub Discussions](https://github.com/ghadamaalej/finops-ai-agent/discussions)
- 🐛 [Report Issues](https://github.com/ghadamaalej/finops-ai-agent/issues)

---

## 🌟 Trusted By

Leading enterprises use FinOps AI Agent to optimize cloud spending and improve margins.

---

<div align="center">

**Reduce cloud spending. Optimize infrastructure. Move faster.**

⭐ If you find this project valuable, please [star it on GitHub](https://github.com/ghadamaalej/finops-ai-agent) ⭐

*Built with ❤️ by developers passionate about cloud efficiency and production-grade infrastructure*

[Get Started](#-quick-start) • [Documentation](https://docs.finopsai.com) • [Enterprise](mailto:enterprise@finopsai.com) • [Kubernetes Deployment](#-deployment--cicd-pipeline)

</div>
