# FinOps AI Agent

[![Python](https://img.shields.io/badge/Python-50.9%25-blue?style=flat-square)](.)
[![TypeScript](https://img.shields.io/badge/TypeScript-46.5%25-2d72b8?style=flat-square)](.)
[![CSS](https://img.shields.io/badge/CSS-2.4%25-563d7c?style=flat-square)](.)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0+-009688?style=flat-square)](.)
[![LangSmith](https://img.shields.io/badge/LangSmith-Integrated-2d72b8?style=flat-square)](https://smith.langchain.com)

An intelligent AI-powered agent for Azure FinOps optimization that analyzes cloud infrastructure, detects inefficiencies, recommends cost-saving actions, and executes approved optimizations—all through a unified, user-friendly platform with comprehensive LLM monitoring via LangSmith.

## 🎯 Overview

**FinOps AI Agent** is an intelligent cloud cost optimization platform built to help organizations manage and reduce Azure spending using AI-driven insights. The project combines a FastAPI backend, AI orchestration with LangChain/LangGraph, Azure cloud monitoring APIs, and a modern dashboard frontend to provide real-time visibility into cloud infrastructure usage, cost trends, and optimization opportunities. 

Powered by **LangSmith**, the platform provides enterprise-grade monitoring of AI agent workflows, performance metrics, and automated evaluation of recommendation accuracy.

### What Makes It Unique

Unlike traditional cost management tools, FinOps AI Agent goes beyond reporting to provide **intelligent recommendations and actionable automation**:

- 🤖 **AI-Powered Analysis** - LangChain/LangGraph orchestrated reasoning to detect complex inefficiencies
- 📊 **Real-Time Insights** - Stream Azure metrics and cost data for up-to-the-minute visibility
- 🎯 **Smart Recommendations** - Contextual optimization suggestions based on workload patterns
- ⚡ **Approved Automation** - Execute cost-saving actions directly on Azure resources with proper authorization
- 🔐 **Enterprise Security** - Role-based access control with secure credential management
- 🛡️ **LLM Reliability** - Comprehensive LangSmith integration for workflow tracing, performance monitoring, and automated evaluation

## 🚀 Core Capabilities

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

## 🛡️ LangSmith Integration - Most Valuable Features

### 🔍 1. Agent Workflow Tracing (High Priority)

**Visualize the execution of your LangGraph nodes with complete visibility:**

Gain deep insights into your AI agent's decision-making pipeline:
- **Azure Observation Node** - Track resource data collection, API calls, and data retrieval performance
- **Cost Analysis Node** - Monitor cost data aggregation, trend calculations, and anomaly detection
- **Security Analysis Node** - Trace security risk detection, compliance checks, and policy validation
- **Recommendation Generation Node** - Observe AI reasoning, LLM calls, cost/benefit analysis, and prioritization
- **Approval Node** - Monitor approval workflow, validation logic, and execution decisions

**Key Benefits:**
- Complete execution DAG visible in LangSmith dashboard
- Per-node execution metrics: latency, tokens, costs
- Real-time error tracking and exception handling
- Input/output inspection for debugging and optimization
- Identify performance bottlenecks in the pipeline
- Full audit trail for compliance and accountability

### 📊 2. Performance & Cost Monitoring (High Priority)

**Track response latency, token consumption, LLM costs, and execution failures to optimize agent efficiency:**

**Response Latency Monitoring**
- End-to-end request latency tracking
- Per-node execution duration breakdown
- Percentile analysis (p50, p95, p99)
- Identify and optimize performance bottlenecks
- SLA tracking and alerting

**Token Consumption Tracking**
- Input/output tokens per LLM call
- Cumulative token usage and trends
- Token efficiency analysis
- Cost optimization through prompt engineering
- Budget tracking and forecasting

**LLM Cost Analysis**
- Real-time cost per recommendation
- Cumulative spending dashboard
- Cost breakdown by model and operation
- ROI analysis: LLM costs vs. optimization savings
- Cost trends and predictive analytics

**Execution Failure Tracking**
- Monitor and alert on failed operations
- Track API errors and retry patterns
- Root cause analysis for failures
- Error rate trends and patterns
- Critical failure notifications

### ✅ 3. Automated Evaluation (High Priority)

**Create test datasets containing Azure scenarios with expected recommendations. Evaluate correctness:**

**Test Dataset Management**
- Create realistic Azure resource scenarios:
  - Overprovisioned VMs with low usage
  - Underutilized databases
  - Unused storage and network resources
  - Reserved instance opportunities
- Define expected recommendations for each scenario
- Version control for evaluation datasets
- Support for regression testing

**Evaluation Framework**
- Automated comparison: AI recommendations vs. expected outputs
- Precision and recall metrics
- Correctness scoring and accuracy rates
- False positive/negative detection
- Recommendation quality assessment

**Continuous Evaluation Pipeline**
- Run evaluations automatically on each deployment
- Track evaluation metrics over time
- A/B testing for different recommendation strategies
- Regression detection for model degradation
- Performance dashboards and trend analysis
- Identify failing test cases and gaps

## 📁 Project Structure

```
finops-ai-agent/
├── api/                        # FastAPI endpoints
│   ├── agent.py               # AI agent analysis & optimization endpoints
│   ├── auth.py                # Authentication and authorization routes
│   ├── dashboard.py           # Dashboard data endpoints
│   └── health.py              # Health check endpoints
├── app/
│   ├── agent/                 # LangGraph orchestration & AI reasoning
│   ├── tools/                 # Azure and FinOps tools for analysis & execution
│   ├── services/              # Business logic layer
│   ├── database/              # Database models and initialization
│   ├── config/                # Settings and logging configuration
│   ├── core/                  # Shared application utilities
│   ├── schemas/               # Pydantic request/response models
│   ├── utils/                 # Helper functions
│   └── mcp/                   # Model Context Protocol integration
├── frontend/                  # React + TypeScript + Tailwind CSS dashboard
├── migrations/                # Database schema migrations
├── config/                    # Application configuration
├── scripts/                   # Utility scripts
├── main.py                    # FastAPI application entry point
├── Dockerfile                 # Container configuration
└── requirements.txt           # Python dependencies
```

## 🛠️ Technology Stack

### Backend
- **FastAPI** (0.111.0+) - Modern, fast Python web framework
- **SQLAlchemy** (2.0.0+) - SQL toolkit and ORM for data persistence
- **LangChain & LangGraph** (0.2.0+) - LLM orchestration and AI workflow reasoning
- **LangSmith** (0.2.0+) - Agent workflow tracing, performance monitoring, and automated evaluation
- **Azure SDK** - Comprehensive Azure service integration:
  - `azure-mgmt-costmanagement` - Cost analysis and billing
  - `azure-mgmt-compute` - VM and resource management
  - `azure-mgmt-monitor` - Metrics and performance data
  - `azure-monitor-query` - Advanced telemetry queries
  - `azure-mgmt-storage` - Storage account management
  - `azure-mgmt-network` - Network resources
  - `azure-mgmt-security` - Security insights
- **Pydantic** (2.7.0+) - Data validation and settings management
- **PyJWT** - Secure token handling

### Frontend
- **React 19** - UI library
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS v4** - Utility-first CSS framework
- **TailAdmin** - Professional dashboard template with prebuilt components

### Infrastructure
- **Docker** - Containerization and deployment
- **PostgreSQL** (12+) - Relational database
- **Uvicorn** (0.30.0+) - ASGI server
- **Python 3.11+** - Runtime

## 🚀 Quick Start

### Prerequisites

- **Python** 3.11 or higher
- **Node.js** 18.x or higher
- **PostgreSQL** 12+ (for database)
- **Azure Subscription** with appropriate permissions
- **OpenAI/Azure OpenAI API Key**
- **LangSmith API Key** (for workflow tracing and evaluation)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ghadamaalej/finops-ai-agent.git
   cd finops-ai-agent
   ```

2. **Set up Python environment:**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your Azure credentials, API keys, and LangSmith credentials
   ```

5. **Initialize the database:**
   ```bash
   python -m app.database.init_db
   ```

6. **Install frontend dependencies:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

### Running the Application

**Start the backend API server:**
```bash
python main.py
```
The API will be available at `http://localhost:8000`

**Start the frontend development server (in a new terminal):**
```bash
cd frontend
npm run dev
```
The frontend will be available at `http://localhost:5173`

**API Documentation:**
Navigate to `http://localhost:8000/docs` for interactive Swagger documentation.

**LangSmith Tracing Dashboard:**
View real-time agent execution traces at your [LangSmith dashboard](https://smith.langchain.com)

## 🔌 API Endpoints

### Health & Status
```
GET  /health      - Service health check
GET  /            - Root endpoint with status
```

### Agent Operations
```
POST /api/agent/analyze                - Analyze costs and get recommendations
POST /api/agent/optimize               - Execute approved optimization actions
POST /api/agent/approve-action         - Approve a specific optimization action
GET  /api/agent/recommendations        - Get pending recommendations
GET  /api/agent/execution-history      - Retrieve action execution history
GET  /api/agent/audit-log              - Get comprehensive audit trail
GET  /api/agent/llm-metrics            - Get LLM performance and tracing metrics
```

### Authentication
```
POST /api/auth/login                   - User login (returns JWT token)
POST /api/auth/logout                  - User logout
POST /api/auth/refresh                 - Refresh authentication token
GET  /api/auth/current-user            - Get current authenticated user info
```

### Dashboard
```
GET  /api/dashboard/metrics            - Get dashboard metrics and KPIs
GET  /api/dashboard/costs              - Get cost data and trends
GET  /api/dashboard/resources          - Get resource inventory and status
GET  /api/dashboard/optimization-summary - Summary of optimization opportunities
GET  /api/dashboard/agent-performance  - Agent workflow and LangSmith metrics
```

### Monitoring
```
GET  /api/monitoring/langsmith/traces  - Retrieve LangSmith trace data
GET  /api/monitoring/performance       - Get system performance metrics
GET  /api/monitoring/evaluation-results - Get automated evaluation results
```

## 🔧 Configuration

### Environment Variables

Essential environment variables (see `.env.example`):

```env
# FastAPI & Server
FASTAPI_ENV=development
DEBUG=false

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/finops_db

# Azure Service Principal Configuration
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# AI/LLM Configuration
OPENAI_API_KEY=your-openai-key
AZURE_OPENAI_API_KEY=your-azure-openai-key
AZURE_OPENAI_ENDPOINT=your-azure-openai-endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# LangSmith Configuration (Agent Tracing, Performance Monitoring, Evaluation)
LANGSMITH_API_KEY=your-langsmith-api-key
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_PROJECT=finops-ai-agent
LANGSMITH_TRACING_ENABLED=true

# Frontend
FRONTEND_ORIGIN=http://localhost:5173

# Security
SECRET_KEY=your-secret-key-for-jwt
JWT_EXPIRATION_HOURS=24

# Logging
LOG_LEVEL=INFO
```

### Azure Permissions Required

The service principal needs the following roles:

- **Cost Management Reader** - For cost analysis
- **Reader** - For resource enumeration
- **Contributor** (or specific resource modification roles) - For executing approved optimizations
- **Security Reader** - For security insights

## 🧪 Testing

Run the test suite:

```bash
# Test Azure OpenAI integration
python test_azure_openai.py

# Test LLM service
python test_llm_service.py

# Test reasoning engine
python test_reason.py

# Run automated evaluations
python -m app.monitoring.evaluation
```

## 🐳 Docker Deployment

### Build the Docker image
```bash
docker build -t finops-ai-agent:latest .
```

### Run the container
```bash
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:password@postgres:5432/finops_db \
  -e AZURE_SUBSCRIPTION_ID=your-id \
  -e AZURE_TENANT_ID=your-tenant-id \
  -e AZURE_CLIENT_ID=your-client-id \
  -e AZURE_CLIENT_SECRET=your-secret \
  -e OPENAI_API_KEY=your-key \
  -e LANGSMITH_API_KEY=your-langsmith-key \
  finops-ai-agent:latest
```

### Docker Compose
```bash
docker-compose up -d
```

## 📊 Database Migrations

Apply pending migrations:
```bash
python -m alembic upgrade head
```

Create a new migration:
```bash
python -m alembic revision --autogenerate -m "Description of changes"
```

## 🔐 Security Considerations

### Critical Security Practices

- **Never commit `.env` files or credentials** to version control
- **Rotate API keys regularly** - Especially Azure service principal and LangSmith credentials
- **Use Azure RBAC** - Grant only necessary permissions to service principals
- **Enable HTTPS/TLS** - All API communications must be encrypted in production
- **Implement request rate limiting** - Protect against brute force and DDoS
- **Audit all actions** - Maintain comprehensive logs of all optimization executions
- **Approval workflow** - Require human approval for resource-modifying actions
- **Encryption** - Sensitive data encrypted at rest and in transit
- **Token management** - Implement token rotation and expiration policies
- **Keep dependencies updated** - Regular security patches for all libraries
- **LangSmith Security** - Protect LangSmith API keys and audit trace access

## 💡 Key Workflows

### Cost Analysis Workflow
1. Agent initiates LangGraph workflow (traced in LangSmith)
2. Azure Observation Node: Queries Azure APIs for resource data
3. Cost Analysis Node: Analyzes patterns and calculates metrics
4. Security Analysis Node: Checks compliance and security issues
5. Recommendation Generation Node: AI generates optimization suggestions
6. LangSmith captures complete execution trace with detailed metrics
7. Performance data logged for monitoring and optimization
8. Results displayed in dashboard

### Optimization Execution Workflow
1. User reviews recommendations in dashboard
2. User selects actions to approve
3. Action sent to approval queue (traced in LangSmith)
4. Approval Node: Verifies action feasibility and prerequisites
5. Upon approval, action executed on Azure resources
6. Execution logged with before/after metrics
7. Cost impact tracked and reported
8. LangSmith evaluates recommendation accuracy against outcomes
9. Continuous improvement metrics recorded

## 🎓 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [LangSmith Tracing Guide](https://docs.smith.langchain.com/monitoring/debugging/tracing)
- [LangSmith Evaluation Guide](https://docs.smith.langchain.com/evaluation)
- [Azure SDK for Python](https://learn.microsoft.com/en-us/python/azure/)
- [Azure FinOps Best Practices](https://learn.microsoft.com/en-us/azure/cost-management-billing/finops/)
- [React Documentation](https://react.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋 Support

For questions, issues, or feedback:

- **GitHub Issues** - [Report bugs or request features](https://github.com/ghadamaalej/finops-ai-agent/issues)
- **GitHub Discussions** - [Start a discussion](https://github.com/ghadamaalej/finops-ai-agent/discussions)
- **Email** - Submit inquiries via GitHub

## ⭐ Show Your Support

If this project has been helpful, please consider:
- Giving it a star ⭐
- Sharing it with others
- Providing feedback and suggestions

---

*Empowering organizations to optimize cloud costs through intelligent automation, AI-driven insights, and comprehensive agent monitoring via LangSmith.*
