# FinOps AI Agent

<p align="center">
  <img src="https://img.shields.io/badge/Python-50.9%25-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/TypeScript-46.5%25-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/CSS-2.4%25-1572B6?style=for-the-badge&logo=css3&logoColor=white" alt="CSS" />
  <img src="https://img.shields.io/badge/AI-FinOps%20Ops-4B5563?style=for-the-badge" alt="AI FinOps" />
  <img src="https://img.shields.io/badge/Status-Production%20Ready-22C55E?style=for-the-badge" alt="Status" />
</p>

<p align="center">
  <strong>Intelligent Azure cost optimization assistant for engineering and finance teams.</strong>
</p>

> FinOps AI Agent helps organizations monitor Azure spend, identify waste, explain cost drivers, and recommend safe optimization actions using AI-powered workflows and observability.

---

## Why this project exists

Cloud cost management often fails because teams work in silos: engineering optimizes performance without visibility into spend, while finance sees the bill but not the usage context. This project closes that gap.

FinOps AI Agent brings together:

- Azure cost and resource intelligence
- AI-driven recommendation generation
- Approval-aware execution workflows
- Structured monitoring and traceability
- Production-ready deployment patterns for private Kubernetes environments

The result is a practical platform for reducing waste without creating operational risk.

---

## Overview

FinOps AI Agent is designed to:

- analyze Azure resource utilization and spend patterns
- surface underused or overprovisioned cloud resources
- explain optimization opportunities in plain language
- support safe automation through review and approval cycles
- provide dashboards and developer-friendly APIs for operational visibility

It is built for teams that want to move faster while keeping cloud governance under control.

---

## Key capabilities

### AI-powered cost recommendations

- Detect underutilized VMs, idle workloads, and oversized resource allocations
- Combine telemetry, metadata, and cost signals for contextual recommendations
- Provide confidence-based suggestions instead of raw cost-only alerts
- Help engineers and finance teams understand the "why" behind optimization decisions

### Safe action workflows

- Approval-based execution for optimization tasks
- Human-in-the-loop review before resource changes are applied
- Clear audit trail for actions taken, decisions made, and outcomes observed
- Better governance for automated cloud optimization

### Operational observability

- LLM workflow tracing and monitoring
- Evaluation of recommendations and execution quality
- Real-time metrics for response times, recommendations, and platform health
- Consolidated views for engineering and cost governance teams

### Production deployment model

- Kubernetes-first architecture
- Proxmox-backed private cluster design
- MetalLB + ingress ingress for service exposure
- Rolling deployment support for zero-downtime updates
- CI/CD automation with validation and deployment gates

---

## Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                         Azure Cloud                          │
│                                                              │
│  • Azure Cost Management                                      │
│  • Resource Graph / Monitor                                   │
│  • Policy / Security / Usage Signals                          │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                 FinOps AI Agent Platform                     │
│                                                              │
│  API Layer                                                  │
│  ├─ FastAPI service                                          │
│  ├─ Agent orchestration                                     │
│  ├─ Azure integrations                                      │
│  ├─ Recommendation engine                                    │
│  ├─ Approval workflow                                       │
│  └─ Monitoring / tracing                                    │
│                                                              │
│  Dashboard Layer                                            │
│  ├─ Cost analytics                                          │
│  ├─ Resource insights                                        │
│  ├─ Recommendation feeds                                     │
│  └─ Audit and execution visibility                           │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│               Kubernetes / Proxmox Production Cluster        │
│                                                              │
│  • API Services                                              │
│  • Frontend Dashboard                                       │
│  • Ingress + Load Balancing                                  │
│  • Autoscaling / health checks                               │
│  • Secrets / config / environment management                 │
└──────────────────────────────────────────────────────────────┘
```

---

## Project structure

```text
finops-ai-agent/
├── app/
│   ├── agent/
│   ├── config/
│   ├── database/
│   ├── services/
│   ├── tools/
│   └── utils/
├── api/
│   ├── agent.py
│   ├── auth.py
│   ├── dashboard.py
│   └── health.py
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── k8s/
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── deployment-api.yaml
│   ├── deployment-frontend.yaml
│   ├── ingress.yaml
│   ├── service-api.yaml
│   ├── service-frontend.yaml
│   └── secrets.yaml
├── .github/
│   └── workflows/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── main.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
└── .env.example
```

---

## Technology stack

### Backend

- Python
- FastAPI
- LangChain / LangGraph
- Azure SDKs
- SQLAlchemy
- PostgreSQL
- LangSmith integration for tracing and evaluation

### Frontend

- TypeScript
- React
- Tailwind CSS
- Modern dashboard components

### Infrastructure

- Docker
- Kubernetes
- Proxmox VE
- MetalLB
- NGINX Ingress
- GitHub Actions

---

## Deployment model

This project is designed for a Kubernetes cluster hosted on Proxmox infrastructure, with the following deployment goals:

- maintain resilience across multiple nodes
- use rolling updates for safer releases
- keep TLS and ingress fronted traffic in a controlled layer
- separate app runtime from configuration and secrets
- support continuous delivery with validation gates

A typical production topology includes:

- one or more control-plane nodes
- worker nodes for application workloads
- a quorum or witness node for high availability safety
- a load balancer layer such as MetalLB
- ingress routing to API and frontend services

---

## Example deployment flow

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: finops-api
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
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
          env:
            - name: AZURE_TENANT_ID
              valueFrom:
                secretKeyRef:
                  name: finops-secrets
                  key: azure-tenant-id
          resources:
            requests:
              cpu: 250m
              memory: 512Mi
            limits:
              cpu: 1
              memory: 1Gi
```

---

## Quick start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker
- Azure subscription access
- Access to desired deployment environment
- Optional: OpenAI and LangSmith credentials for AI features

### Clone the repository

```bash
git clone https://github.com/ghadamaalej/finops-ai-agent.git
cd finops-ai-agent
```

### Backend setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Frontend setup

```bash
cd frontend
npm install
npm run dev
```

### Run the application

```bash
cd ..
python main.py
```

---

## Environment variables

A typical `.env` should include values for:

```env
AZURE_SUBSCRIPTION_ID=
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
OPENAI_API_KEY=
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=
DATABASE_URL=
APP_ENV=development
```

---

## Security and governance

This project is intended for environments where governance matters. Recommended practices include:

- least-privilege Azure identities
- scoped RBAC and resource access
- secret management through environment variables or secret stores
- secure logging and audit tracking
- approval gates for any production-affecting automation
- image scanning and environment checks in CI/CD

---

## CI/CD and quality gates

GitHub Actions can be used to enforce:

- linting and static analysis
- automated tests
- dependency checks
- Docker image builds
- security scans
- staging validation
- production deployment approval

The goal is to minimize risky changes while shipping improvements confidently.

---

## Use cases

### Engineering teams

- reduce unused compute spend
- find oversized VM or capacity mismatches
- get actionable recommendations without doing manual spreadsheet analysis

### Finance teams

- track cost anomalies and forecast trends
- understand business impact of cloud usage
- align engineering effort with cost accountability

### Platform teams

- standardize resource optimization workflows
- improve governance and operational consistency
- monitor deployment health and recommendation quality

---

## Roadmap

Planned focus areas include:

- broader Azure service coverage
- richer recommendation scoring and explainability
- deeper execution guardrails and policy support
- stronger dashboard analytics and custom reporting
- more production-ready Kubernetes operational patterns
- extended observability metrics and evaluation pipelines

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contributing

Contributions are welcome. If you are improving the product, adding cost analysis capabilities, strengthening deployment workflows, or improving the dashboard, please open an issue or submit a pull request.

---

## Support

For questions, suggestions, or deployment discussions, use the repository issues and discussions area.

---

<p align="center">
  <strong>Reduce waste. Improve visibility. Scale with confidence.</strong>
</p>
