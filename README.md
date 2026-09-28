# FinOps AI Agent

[![Python](https://img.shields.io/badge/Python-50.9%25-blue?style=flat-square)](.)
[![TypeScript](https://img.shields.io/badge/TypeScript-46.5%25-2d72b8?style=flat-square)](.)
[![CSS](https://img.shields.io/badge/CSS-2.4%25-563d7c?style=flat-square)](.)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0+-009688?style=flat-square)](.)
[![LangSmith](https://img.shields.io/badge/LangSmith-Integrated-2d72b8?style=flat-square)](https://smith.langchain.com)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Production-326ce5?style=flat-square)](.)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)]()

> Intelligent AI-powered platform for Azure cloud cost optimization with enterprise-grade monitoring, workflow tracing, recommendation evaluation, and production-ready Kubernetes deployment on Proxmox infrastructure.

---

## Overview

FinOps AI Agent is an intelligent cloud optimization platform designed to reduce Azure waste, improve cost visibility, and automate safe optimization decisions using AI. It combines Azure cost analysis, telemetry monitoring, secure governance, and LangGraph-based reasoning with a modern control plane and production-grade Kubernetes deployment model.

This project is built for organizations that need:
- real-time Azure cost insights
- AI-assisted optimization recommendations
- controlled execution of approved actions
- infrastructure reliability on private Proxmox-backed Kubernetes clusters
- automated CI/CD deployment workflows

---

## Why This Project Matters

Cloud cost inefficiency is one of the most common sources of waste in modern organizations. Teams frequently face:
- overprovisioned virtual machines
- unused or low-utilization resources
- fragmented visibility into cloud spend
- slow manual review of optimization opportunities
- limited governance around automated actions

FinOps AI Agent solves this by combining:
- Azure monitoring and cost APIs
- AI-driven recommendations
- approval-based execution
- LLM tracing and evaluation
- resilient Kubernetes deployment architecture

---

## Core Capabilities

### AI-Driven Cost Intelligence
- identifies overprovisioned or underutilized Azure resources
- analyzes cost, metrics, and trend data
- detects anomalies and optimization opportunities
- recommends savings with confidence scoring

### Approved Azure Actions
- execute safe optimization actions only after approval
- support for VM resizing, resource cleanup, and policy-based optimization
- full audit history for accountability and compliance

### Executive Dashboard
- unified cost and infrastructure visibility
- role-based views for finance, engineering, and operations
- real-time metrics and optimization summaries

### LangSmith Monitoring
- trace agent workflow execution end-to-end
- monitor LLM latency, token usage, and response quality
- track performance and recommendation accuracy
- automate evaluation against expected Azure-finops scenarios

### Production Deployment Infrastructure
- Proxmox-based private Kubernetes cluster
- master + worker + QDevice topology
- MetalLB for bare-metal load balancing
- NGINX Ingress for routing and TLS
- rolling update strategy for zero-downtime deployments
- GitHub Actions CI/CD automation

---

## Architecture

```text
Azure Cloud
   │
   ├── Cost Management APIs
   ├── Resource Manager APIs
   ├── Monitor / Metrics APIs
   └── Security / Policy Insights
   │
   ▼
FinOps AI Agent
   ├── FastAPI backend
   ├── LangGraph orchestration
   ├── Azure data tools
   ├── LLM reasoning layer
   ├── approval workflow
   └── dashboards + API endpoints
   │
   ▼
Kubernetes Cluster (Proxmox)
   ├── Master Node
   ├── Worker Node
   ├── QDevice / quorum node
   ├── MetalLB
   ├── NGINX Ingress
   └── Rolling Deployment Strategy
Proxmox Infrastructure Design
3-Node Cluster
This deployment model supports a private, resilient, on-prem Kubernetes environment using Proxmox VE.

Master node
kube-apiserver
scheduler
controller-manager
etcd coordination
Worker node
workload execution
container runtime
application services
QDevice / quorum node
supports cluster quorum and election safety
improves resilience during split-brain conditions
High Availability Features
multiple control and worker nodes
resilient scheduling
health checks and pod restarts
persistent volumes for database and state
backup-ready storage strategy
Load Balancing
MetalLB provides load balancing for bare-metal Kubernetes
assigns external IPs from a configured pool
enables service exposure without cloud-managed load balancers
Ingress
NGINX Ingress Controller handles traffic routing
path-based routing and host-based routing
TLS termination
rate limiting, retries, and security policies
Rolling Update Strategy
The application is designed to support zero-downtime deployments:

YAML
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 0
    maxSurge: 1
Benefits:

no application downtime during updates
safer production rollout
easier rollback when issues occur
efficient progressive delivery
GitHub Actions CI/CD Pipeline
The project is designed for automated deployment via GitHub Actions with a secure and production-friendly flow.

Example pipeline flow
Text
push to main / develop
        │
        ▼
1. lint + format checks
2. unit tests + integration tests
3. build Docker images
4. security scan
5. push to registry
6. deploy to staging
7. manual approval
8. deploy to production
9. smoke tests
10. monitoring + rollback support
Typical workflow stages
code validation
dependency checks
test execution
image build
vulnerability scan
staging deployment
production deployment
health verification
alert notification
Kubernetes Deployment Example
Deployment manifest
YAML
apiVersion: apps/v1
kind: Deployment
metadata:
  name: finops-ai-agent
  namespace: production
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  selector:
    matchLabels:
      app: finops-ai-agent
  template:
    metadata:
      labels:
        app: finops-ai-agent
    spec:
      containers:
        - name: finops-ai-agent
          image: finops-ai-agent:latest
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: finops-secrets
                  key: database-url
            - name: OPENAI_API_KEY
              valueFrom:
                secretKeyRef:
                  name: finops-secrets
                  key: openai-api-key
          resources:
            requests:
              cpu: "250m"
              memory: "512Mi"
            limits:
              cpu: "1"
              memory: "1Gi"
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 20
            periodSeconds: 10
Service with MetalLB
YAML
apiVersion: v1
kind: Service
metadata:
  name: finops-ai-agent-service
  namespace: production
  annotations:
    metallb.universe.tf/address-pool: default
spec:
  type: LoadBalancer
  selector:
    app: finops-ai-agent
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
Ingress with NGINX
YAML
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: finops-ai-agent-ingress
  namespace: production
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
spec:
  ingressClassName: nginx
  rules:
    - host: finops.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: finops-ai-agent-service
                port:
                  number: 80
LangSmith Features
Agent Workflow Tracing
visualize LangGraph execution flow
inspect Azure observation, analysis, recommendation, and approval nodes
debug decision flow and performance issues
Performance & Cost Monitoring
track latency and cost per request
monitor token usage
detect inefficient prompts or expensive operations
review failures and bottlenecks
Automated Evaluation
create Azure scenario datasets with expected outcomes
check recommendation correctness
detect hallucinations and unsupported recommendations
compare model quality over time
Technology Stack
Backend
Python
FastAPI
SQLAlchemy
LangChain
LangGraph
LangSmith
Azure SDKs
Frontend
React
TypeScript
Tailwind CSS
TailAdmin dashboard UI
Infrastructure
Proxmox VE
Kubernetes
MetalLB
NGINX Ingress
Docker
PostgreSQL
GitHub Actions
Project Structure
Text
finops-ai-agent/
├── api/
├── app/
│   ├── agent/
│   ├── tools/
│   ├── services/
│   ├── database/
│   ├── config/
│   └── utils/
├── frontend/
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── namespace.yaml
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── Dockerfile
├── main.py
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore
Quick Start
Prerequisites
Python 3.11+
Node.js 18+
PostgreSQL
Azure subscription credentials
OpenAI or Azure OpenAI API credentials
Kubernetes cluster access (for deployment)
LangSmith API key (optional, for monitoring)
Local Setup
bash
git clone https://github.com/ghadamaalej/finops-ai-agent.git
cd finops-ai-agent

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

cd frontend
npm install
cd ..

python main.py
Frontend
bash
cd frontend
npm run dev
API Endpoints
GET /health
GET /
POST /api/agent/analyze
POST /api/agent/optimize
GET /api/agent/recommendations
GET /api/dashboard/metrics
GET /api/dashboard/resources
GET /api/monitoring/langsmith/traces
Security & Governance
secure Azure credential handling
human approval before resource-changing actions
RBAC-based access control
audit logging of actions and recommendations
TLS for production traffic
secrets management in Kubernetes
CI/CD image scanning and security validation
Roadmap
multi-cloud support (AWS / GCP)
advanced forecasting models
deeper cost allocation and chargeback
more automated optimization actions
more advanced policy enforcement
broader Proxmox deployment hardening and backup strategy
License
This project is licensed under the MIT License.

Contact
GitHub: ghadamaalej
Repository: ghadamaalej/finops-ai-agent
Final Value Proposition
FinOps AI Agent is not just a monitoring tool or dashboard. It is an AI-driven FinOps platform with:

Azure cost intelligence
automated recommendations
human-in-the-loop controls
LangSmith observability
private Proxmox Kubernetes production deployment
GitHub Actions automated release workflow
It is built to reduce cloud waste, improve governance, and support production-grade operations in real environments.

