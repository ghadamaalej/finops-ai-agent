# FinOps AI Agent

[![Python](https://img.shields.io/badge/Python-50.9%25-blue?style=flat-square)](.)
[![TypeScript](https://img.shields.io/badge/TypeScript-46.5%25-2d72b8?style=flat-square)](.)
[![CSS](https://img.shields.io/badge/CSS-2.4%25-563d7c?style=flat-square)](.)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0+-009688?style=flat-square)](.)
[![LangSmith](https://img.shields.io/badge/LangSmith-Integrated-2d72b8?style=flat-square)](https://smith.langchain.com)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)]()

> **Intelligent AI-powered platform for Azure cloud cost optimization with enterprise-grade monitoring, comprehensive agent workflow tracing, and automated recommendation evaluation.**

---

## 🎯 Executive Summary

**FinOps AI Agent** is a production-ready cloud cost optimization platform that leverages advanced AI reasoning to identify inefficiencies in Azure infrastructure and execute cost-saving actions with human oversight. Built for enterprise teams, it combines intelligent analysis with actionable automation to reduce unnecessary cloud spending while maintaining security and compliance.

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

### Key Impact
- **Reduce cloud spending** by 15-30% through intelligent optimization
- **Decrease manual work** with automated detection and execution
- **Maintain control** with approval workflows and comprehensive audit logs
- **Ensure reliability** with LLM monitoring and continuous evaluation

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

### For Executive Leadership
- **Strategic Cost Reduction** - Move beyond reporting to actionable optimization
- **Competitive Advantage** - Reduce cloud spending, improve margins, scale faster
- **Risk Mitigation** - Enterprise-grade controls, audit trails, and security
- **Data-Driven Decisions** - Powered by AI analysis of your actual infrastructure
- **Scalable Solution** - Handles multi-team, multi-subscription Azure environments

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
├── migrations/                # Database migrations
├── main.py                    # Entry point
└── requirements.txt           # Dependencies
```

---

## 🛠️ Technology Stack

**Backend:** FastAPI • SQLAlchemy • LangChain/LangGraph • LangSmith • Azure SDK
**Frontend:** React 19 • TypeScript • Tailwind CSS v4 • TailAdmin
**Infrastructure:** Docker • PostgreSQL • Python 3.11+

---

## 📈 Use Cases & ROI

### Use Case 1: Large Enterprises
**Scenario:** Fortune 500 company with $50M annual Azure spend across 50+ subscriptions

**Results:**
- Identify $8-12M annual savings (16-24% reduction)
- Reduce manual analysis time from 500 hours/year to 50 hours/year
- Maintain governance with approval workflows and audit trails
- **Payback Period:** < 3 months

### Use Case 2: Scaling Startups
**Scenario:** High-growth company with unpredictable spend, $500K-$2M annual Azure

**Results:**
- Eliminate wasted dev/test resources: $50-150K/year
- Optimize production infrastructure: $30-100K/year
- Prevent future waste through continuous monitoring
- **Payback Period:** < 1 month

### Use Case 3: MSPs & Cloud Consultants
**Scenario:** Service provider managing 100+ customer Azure environments

**Results:**
- Add cost optimization as a managed service offering
- $200-500 per customer per month in identified savings
- Increase customer retention and account expansion
- **New Revenue Stream:** Yes

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+, Node.js 18+, PostgreSQL 12+
- Azure Subscription with appropriate permissions
- OpenAI/Azure OpenAI API Key
- LangSmith API Key (optional, for monitoring)

### Installation
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

# Run
python main.py  # Backend at http://localhost:8000
cd frontend && npm run dev  # Frontend at http://localhost:5173
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
- **SOC 2 Ready** - Built with enterprise security practices

---

## 📈 Roadmap

- **Phase 2:** Multi-cloud support (AWS, GCP), advanced forecasting, chargeback/cost allocation
- **Phase 3:** Mobile app, ServiceNow integration, custom policies, ML-powered anomaly detection
- **Phase 4:** Generative insights, autonomous optimization, cross-cloud resource optimization

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

*Built with ❤️ by developers passionate about cloud efficiency*

[Get Started](#-quick-start) • [Documentation](#-learning-resources) • [Enterprise](mailto:enterprise@finopsai.com)

</div>
