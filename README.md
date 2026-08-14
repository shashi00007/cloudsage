# CloudSage — GenAI-Powered Cloud Operations & Cost Intelligence Assistant

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)
![AWS Boto3](https://img.shields.io/badge/AWS%20Boto3-1.34%2B-FF9900.svg)
![Status](https://img.shields.io/badge/status-Phase%203%20Complete-green.svg)

**CloudSage** is an intelligent, local AI assistant designed to inspect AWS cloud infrastructure, monitor operational telemetry, and analyze cost breakdowns using natural language queries grounded in real AWS services.

---

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Phase 3 — GenAI Agent & Tool Calling](#phase-3--genai-agent--tool-calling)
  - [LLM Architecture & Providers](#llm-architecture--providers)
  - [Tool Calling Workflow](#tool-calling-workflow)
  - [Available AI Tools](#available-ai-tools)
  - [Safe Development Mock Mode](#safe-development-mock-mode)
  - [Chat API Specification](#chat-api-specification)
  - [Conversation Context & Memory](#conversation-context--memory)
  - [Example Questions & Prompts](#example-questions--prompts)
- [Supported AWS Services (Phase 2 & 3)](#supported-aws-services-phase-2--3)
- [AWS Credentials & Configuration](#aws-credentials--configuration)
- [Required IAM Permissions](#required-iam-permissions)
- [API Endpoints Reference](#api-endpoints-reference)
- [Example API Responses](#example-api-responses)
- [Local Setup Guide](#local-setup-guide)
- [Running Tests](#running-tests)
- [Security Model & Guarantees](#security-model--guarantees)
- [Project Roadmap](#project-roadmap)

---

## Overview

CloudSage acts as an intelligent site reliability engineer and FinOps copilot directly on your local machine. Instead of navigating the complex AWS Management Console or writing one-off CLI commands, users can ask natural language questions and receive accurate, context-aware answers backed by actual AWS telemetry.

### Example Queries CloudSage Answers:
* *"What EC2 instances are currently running?"*
* *"Show me my S3 buckets."*
* *"What is the CPU utilization of my EC2 instance?"*
* *"How much am I spending on AWS and which service costs the most?"*
* *"Give me a summary of my cloud infrastructure and costs."*

---

## Architecture

CloudSage employs a modular, tool-calling agent architecture with strict isolation between operational execution tools and the GenAI reasoning layer.

```
User / Frontend Chat UI
          │  POST /api/chat
          ▼
┌──────────────────────────────────────────────────────────┐
│                  FastAPI Chat Route                      │
│                 (app/routes/chat.py)                     │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│               CloudSage GenAI Agent                      │
│                 (app/ai/agent.py)                        │
│   • In-Memory Multi-Turn Session Memory Store            │
│   • LLM Tool Requirement Evaluation & Dispatch           │
└──────────────┬────────────────────────────┬──────────────┘
               │                            │
               ▼                            ▼
┌──────────────────────────────┐ ┌─────────────────────────┐
│     LLM Provider Engine      │ │    AWS Tool Router      │
│      (app/ai/llm.py)         │ │ (app/ai/tool_router.py) │
│  • OpenAI (GPT-4o-mini)      │ │  ├── inspect_ec2        │
│  • Google Gemini (1.5 Flash) │ │  ├── explore_s3         │
│  • Local Deterministic Engine│ │  ├── get_cloudwatch_... │
└──────────────┬───────────────┘ │  └── analyze_cloud_cost │
               │                 └──────────┬──────────────┘
               │                            │
               │               ┌────────────┴─────────────┐
               │               │                          │
               │    AWS_MOCK_MODE=false        AWS_MOCK_MODE=true
               │               ▼                          ▼
               │       AWS Boto3 Services         Realistic Mock Data
               │     (EC2, S3, CW, Cost)          (Safe Offline Mode)
               │               │                          │
               │               └────────────┬─────────────┘
               │                            │
               ▼                            ▼
┌──────────────────────────────────────────────────────────┐
│          Structured Synthesis & Answer Generation        │
│    (Clear formatting, metrics, disclaimers, FinOps)      │
└────────────────────────────┬─────────────────────────────┘
                             │ JSON Response
                             ▼
                 Frontend AI Assistant UI
```

---

## Phase 3 — GenAI Agent & Tool Calling

### LLM Architecture & Providers

CloudSage features a **clean provider abstraction** in `app/ai/llm.py` that decouples the application from any single AI vendor:
1. **OpenAI**: Native function calling using `gpt-4o-mini` or any configured model.
2. **Google Gemini**: Native function calling using `gemini-1.5-flash` or `gemini-2.0-flash`.
3. **Local Reasoning Engine**: Fast, deterministic offline reasoning engine with intent classification, multi-tool detection, and contextual pronoun resolution. Allows full development without third-party API keys.

All API keys are loaded strictly from environment variables (`.env`). No keys are hardcoded, logged, or exposed to the client.

---

### Tool Calling Workflow

```
User Query: "What EC2 instances are running?"
   │
   ▼
FastAPI `/api/chat`
   │
   ▼
CloudSage Agent
   │
   ▼
LLM / Reasoning Engine determines tool required: `inspect_ec2`
   │
   ▼
Tool Router executes `inspect_ec2` (Boto3 or Mock)
   │
   ▼
Tool returns structured inventory: 3 instances (2 running, 1 stopped)
   │
   ▼
LLM Synthesizes human-friendly response with metrics & disclaimer
   │
   ▼
Response returned to frontend with `tools_used: ["inspect_ec2"]` and `data_source: "mock"`
```

The LLM never directly touches AWS credentials; only backend tools communicate with AWS.

---

### Available AI Tools

| Tool Name | Module | Parameters | Description |
| :--- | :--- | :--- | :--- |
| `inspect_ec2` | `app.tools.ec2` | *None* | Retrieves running and available EC2 instances, states, types, AZs, IPs, and Name tags. |
| `explore_s3` | `app.tools.s3` | *None* | Lists S3 buckets with creation dates. |
| `get_cloudwatch_metrics` | `app.tools.cloudwatch` | `instance_id` (str), `hours` (int, default 1) | Retrieves CPU utilization datapoints, average CPU, min, and peak spike. |
| `analyze_cloud_cost` | `app.tools.cost_explorer` | `days` (int, default 30) | Retrieves AWS spend, total cost, currency, top cost driver, and service breakdown. |

---

### Safe Development Mock Mode

When `AWS_MOCK_MODE=true` (or when AWS credentials are unconfigured):
* Tools return realistic, high-fidelity sample data.
* Responses are flagged internally with `data_source: "mock"`.
* The AI response explicitly states:
  > *"Development mock data is being used because AWS is not connected."*
* When `AWS_MOCK_MODE=false`, CloudSage connects to real AWS APIs via Boto3.

---

### Chat API Specification

#### `POST /api/chat`
**Request Payload:**
```json
{
  "message": "What EC2 instances are currently running?",
  "session_id": "optional-uuid"
}
```

**Response Payload:**
```json
{
  "answer": "### 🖥️ EC2 Instances Overview (us-east-1)\nFound **3 instance(s)** (2 running, 1 stopped):\n- **i-03fa78bc91204d8ef** (`web-prod-01`): RUNNING • Type: `t3.medium`\n- **i-09b62a488e1709c31** (`api-prod-02`): RUNNING • Type: `t3.large`\n- **i-07e155bc90082a17f** (`worker-batch-03`): STOPPED • Type: `c6i.xlarge`\n\n> ℹ️ *Development mock data is being used because AWS is not connected.*",
  "tools_used": ["inspect_ec2"],
  "data_source": "mock",
  "session_id": "3f678287-2178-433b-826d-317424683a37",
  "tool_results": [...]
}
```

#### `POST /api/chat/reset`
**Request Payload:**
```json
{
  "session_id": "3f678287-2178-433b-826d-317424683a37"
}
```

---

### Conversation Context & Memory

CloudSage maintains lightweight in-memory session history:
* **Turn 1:** User asks *"What EC2 instances are running?"* -> CloudSage returns instances.
* **Turn 2:** User asks *"Which one has the highest CPU?"* -> CloudSage remembers the instance IDs from Turn 1, invokes `get_cloudwatch_metrics`, and answers accurately.

---

### Example Questions & Prompts

* 🖥️ **"What EC2 instances are running?"** -> Invokes `inspect_ec2`
* 🪣 **"Show me my S3 buckets."** -> Invokes `explore_s3`
* 💰 **"How much am I spending?"** -> Invokes `analyze_cloud_cost`
* 📊 **"Which AWS service is costing me the most?"** -> Invokes `analyze_cloud_cost` and highlights top driver
* ⚡ **"Give me a cloud health summary."** -> Multi-tool execution (`inspect_ec2` + `explore_s3` + `analyze_cloud_cost`)
* 📈 **"Which EC2 instances are running and what is their CPU utilization?"** -> Multi-tool execution (`inspect_ec2` + `get_cloudwatch_metrics`)

---

## Supported AWS Services (Phase 2 & 3)

| Service | Tool Module | Operations Supported |
| :--- | :--- | :--- |
| **AWS STS** | `app.services.aws_session` | Identity verification, account discovery, connectivity status (`GetCallerIdentity`). |
| **Amazon EC2** | `app.tools.ec2` | Read-only instance inventory, instance types, running states, AZs, private/public IPs, and Name tags. |
| **Amazon S3** | `app.tools.s3` | Read-only bucket listing and creation timestamps (zero object access/download). |
| **Amazon CloudWatch** | `app.tools.cloudwatch` | CPU utilization metric telemetry, average/max/min statistics across configurable time windows. |
| **AWS Cost Explorer** | `app.tools.cost_explorer` | Unblended cost aggregations, total estimated spend, and service-level cost breakdowns. |

---

## AWS Credentials & Configuration

CloudSage uses the **standard AWS credential chain** via `boto3`. You can configure credentials using any standard method:

### Method 1: AWS CLI Credentials (Recommended)
```bash
aws configure
```

### Method 2: Local Environment Variables (`.env`)
```bash
# App Configuration
APP_NAME=CloudSage
APP_ENV=development
AWS_MOCK_MODE=true

# AWS Credentials (when AWS_MOCK_MODE=false)
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# LLM Configuration
LLM_PROVIDER=openai
LLM_API_KEY=your_key_here
LLM_MODEL=gpt-4o-mini
```

---

## Required IAM Permissions

For local development and least-privilege security, create an IAM policy with the following **read-only** permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudSageReadOnlyOperations",
      "Effect": "Allow",
      "Action": [
        "sts:GetCallerIdentity",
        "ec2:DescribeInstances",
        "ec2:DescribeTags",
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:GetMetricData",
        "cloudwatch:ListMetrics",
        "ce:GetCostAndUsage",
        "ce:GetDimensionValues"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## API Endpoints Reference

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/health` | `GET` | Application health and server diagnostic. |
| `/api/aws/status` | `GET` | Tests communication with AWS via STS `GetCallerIdentity`. |
| `/api/chat` | `POST` | Primary AI interaction endpoint. |
| `/api/aws/ec2/instances` | `GET` | Retrieves all EC2 instances in the configured region. |
| `/api/aws/s3/buckets` | `GET` | Lists all S3 buckets in the account with creation dates. |
| `/api/aws/cloudwatch/ec2/{id}/cpu` | `GET` | Returns CPU utilization metrics for an instance (`?hours=1`). |
| `/api/aws/cost/summary` | `GET` | Returns Cost Explorer summary and service spend (`?days=30`). |
| `/docs` | `GET` | Interactive Swagger OpenAPI documentation. |

---

## Example API Responses

### 1. AWS Connection Status (`GET /api/aws/status`)
```json
{
  "connected": true,
  "account_id": "123456789012",
  "arn": "arn:aws:iam::123456789012:user/cloudsage-admin",
  "region": "us-east-1",
  "error_type": null,
  "message": "AWS connection successful"
}
```

### 2. EC2 Instances (`GET /api/aws/ec2/instances`)
```json
{
  "success": true,
  "region": "us-east-1",
  "count": 1,
  "instances": [
    {
      "instance_id": "i-0123456789abcdef0",
      "name": "web-prod-01",
      "instance_type": "t3.micro",
      "state": "running",
      "availability_zone": "us-east-1a",
      "private_ip": "172.31.16.50",
      "public_ip": "54.210.10.20",
      "launch_time": "2026-01-15T10:00:00+00:00"
    }
  ],
  "error": null
}
```

### 3. S3 Buckets (`GET /api/aws/s3/buckets`)
```json
{
  "success": true,
  "count": 2,
  "buckets": [
    {
      "name": "cloudsage-data-lake-prod",
      "creation_date": "2026-01-10T12:00:00+00:00"
    },
    {
      "name": "cloudsage-app-backups",
      "creation_date": "2026-03-05T15:30:00+00:00"
    }
  ],
  "error": null
}
```

### 4. Cost Summary (`GET /api/aws/cost/summary?days=30`)
```json
{
  "success": true,
  "start_date": "2026-07-15",
  "end_date": "2026-08-14",
  "total_cost": 250.00,
  "currency": "USD",
  "top_service": "Amazon Elastic Compute Cloud - Compute",
  "service_count": 2,
  "services": [
    {
      "service": "Amazon Elastic Compute Cloud - Compute",
      "cost": 180.50,
      "percentage": 72.2
    },
    {
      "service": "Amazon Simple Storage Service",
      "cost": 69.50,
      "percentage": 27.8
    }
  ],
  "error": null
}
```

---

---

## Phase 4 — RAG & Cloud Knowledge Intelligence

CloudSage features a locally runnable **Retrieval-Augmented Generation (RAG)** knowledge engine grounded in official AWS documentation. CloudSage answers architectural, security, monitoring, and FinOps questions with verified source citations, while seamlessly combining live AWS operational tools for hybrid query execution.

### RAG Architecture Flow

```text
User Question
    │
    ▼
CloudSage Agent (app/ai/agent.py)
    │
    ├─── Operational Query ──► AWS Tool Router (EC2, S3, CloudWatch, Cost Explorer)
    │                                │
    ├─── Knowledge Inquiry ──► Knowledge Retriever (app/rag/retriever.py)
    │                                │
    │                                ▼
    │                        Vector Store (Cosine Similarity Search)
    │                                │
    │                                ▼
    │                        Relevant AWS Documentation Chunks
    │                                │
    ▼                                ▼
Unified LLM Synthesis & Grounding Engine (OpenAI / Gemini / Local Engine)
    │
    ▼
Grounded Natural Language Response with Source Citations
    │
    ▼
CloudSage Modern UI (📚 Knowledge Base / 🔧 Tool Badges & Sources Box)
```

### Knowledge Base Taxonomy

The curated local dataset in [app/rag/documents.py](file:///c:/Users/iamsh/OneDrive/Desktop/CloudSage/app/rag/documents.py) covers:

1. **Amazon EC2**:
   * EC2 Architecture & Fundamentals
   * Instance Types (General Purpose, Compute, Memory, Storage, Accelerated)
   * Stateful Security Groups vs Stateless Network ACLs
   * Regions, Availability Zones & High Availability
   * Common Causes of High CPU & Troubleshooting
2. **Amazon S3**:
   * S3 Object Storage Fundamentals & 11 9's Durability
   * Storage Classes (Standard, Intelligent-Tiering, Standard-IA, Glacier Instant/Flexible/Deep Archive)
   * Lifecycle Configuration (Transitions, Expirations, Multipart cleanup)
3. **Amazon CloudWatch**:
   * Metrics, Dimensions, Periods, and Statistics
   * Alarms (OK, ALARM, INSUFFICIENT_DATA) and Automated Actions
4. **AWS Identity & Access Management (IAM)**:
   * Users, Groups, Roles, and Temporary STS Credentials
   * JSON Policy Evaluation Logic & Default Deny
   * The Principle of Least Privilege
5. **AWS Cost Management & FinOps**:
   * AWS Cost Explorer & Spending Analysis
   * Well-Architected Cost Optimization Pillar
   * Common Cloud Cost Drivers & Rightsizing Strategies

### Ingestion Pipeline & Rebuilding the Index

Ingest or rebuild the local vector store index at any time with a single command:

```bash
python -m app.rag.ingest
```

This repeatable pipeline:
1. Loads curated AWS knowledge documents.
2. Cleans text and splits into semantic chunks with 40-word overlap.
3. Computes normalized dense semantic vector embeddings.
4. Serializes the vector index and metadata atomically to `./data/vector_store/index.json`.

### Direct Knowledge Search API

Query the vector store directly via HTTP:

* **Endpoint:** `GET /api/rag/search?q={query}&top_k=3`
* **Response:**
  ```json
  {
    "query": "security group",
    "count": 2,
    "results": [
      {
        "chunk_id": "doc_ec2_security_groups_chunk_0",
        "document_id": "doc_ec2_security_groups",
        "title": "EC2 Security Groups and Network Access Rules",
        "category": "EC2",
        "source": "AWS Documentation — Amazon EC2 Security Groups",
        "url": "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html",
        "score": 0.5445,
        "content": "An Amazon EC2 security group acts as a virtual, stateful firewall..."
      }
    ]
  }
  ```

---

## Local Setup Guide

1. **Activate the virtual environment:**
   * PowerShell: `.venv\Scripts\Activate.ps1`
   * Bash: `source .venv/bin/activate`

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ingest the Knowledge Base (Automatic on first run):**
   ```bash
   python -m app.rag.ingest
   ```

4. **Start the local development server:**
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

5. **Access the Application:**
   * **Web Dashboard:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
   * **Swagger API Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Running Tests

Run the full automated test suite using `pytest`:

```bash
pytest tests/ -v
```

All 45 unit, integration, RAG, and agent tool-calling tests run with zero external network dependencies.

---

## Security Model & Guarantees

* **Strictly Read-Only:** CloudSage cannot create, modify, stop, or terminate any AWS infrastructure.
* **No Secret Exposure:** Secret access keys and tokens are never returned by API routes or rendered in the frontend.
* **Untrusted Context Guardrails:** RAG documents are treated as untrusted text; system instructions and safety rules cannot be overridden by retrieved context.
* **Standard Credential Resolution:** Operates seamlessly with IAM roles, AWS SSO, and standard profile files.
* **Local Loopback Only:** Runs strictly on `127.0.0.1`.

---

## Project Roadmap

| Milestone | Status | Description |
| :--- | :---: | :--- |
| **Phase 1: Project Scaffolding** | **Completed** | FastAPI architecture, `/health` endpoint, and initial dashboard. |
| **Phase 2: Real AWS Integration** | **Completed** | Boto3 tools for STS, EC2, S3, CloudWatch, and Cost Explorer with UI test panels. |
| **Phase 3: GenAI Agent & Tool Router** | **Completed** | Autonomous tool-calling agent, memory, mock mode, and AI Assistant UI. |
| **Phase 4: Knowledge RAG & Local DB** | **Completed** | Vector store, semantic embeddings, grounded generation, source citations, and hybrid agent integration. |
| **Phase 5: Interactive Assistant UI** | *Upcoming* | Natural language chat interface with rich charts and cloud insights. |


