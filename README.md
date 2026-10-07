

```markdo
# ☁️ CloudSage — GenAI Cloud Operations Assistant

> A natural-language AI assistant for AWS cloud operations, monitoring, and cost intelligence.

CloudSage lets users interact with AWS infrastructure using natural language instead of manually navigating the AWS Console or writing CLI commands.

It combines:

- 🤖 LLM-based reasoning
- 🔧 AWS tool calling
- 📚 Retrieval-Augmented Generation (RAG)
- 💰 Cloud cost analysis
- 🛡️ Read-only AWS access
- 🧪 Safe mock/sandbox mode
- 🧠 Multi-turn conversation context
- ✅ Automated testing

---

## 🎯 What Problem Does CloudSage Solve?

Managing cloud infrastructure often requires switching between multiple AWS services and understanding large amounts of technical information.

CloudSage provides a conversational interface where users can ask questions such as:

> "What EC2 instances are currently running?"

> "Which instance has the highest CPU utilization?"

> "How much am I spending on AWS?"

> "Which AWS service is costing me the most?"

> "Give me a summary of my cloud infrastructure."

The system determines what information is required, selects the appropriate tool or knowledge source, retrieves the information, and generates a natural-language response.

---

# 🏗️ Architecture

```text
                         USER
                           │
                           ▼
                    Frontend Chat UI
                           │
                           │ POST /api/chat
                           ▼
                    ┌───────────────┐
                    │    FastAPI    │
                    │  Chat Route  │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ CloudSage     │
                    │     Agent     │
                    └───────┬───────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
       LLM / Reasoning              AWS Tool Router
          Provider                       │
              │                    ┌──────┼────────┐
              │                    │      │        │
              │                   EC2    S3   CloudWatch
              │                                      │
              │                                Cost Explorer
              │
              └─────────────┬────────────────────────┘
                            │
                            ▼
                    Structured Results
                            │
                            ▼
                    Response Generation
                            │
                            ▼
                           USER
```

CloudSage separates the AI reasoning layer from AWS execution tools.

The LLM decides what information or tool is required, while the backend tool layer handles AWS communication.

**The LLM never directly accesses AWS credentials.**

---

# 🧠 LLM Provider Architecture

CloudSage uses a provider abstraction so the application is not tightly coupled to a single AI provider.

Current supported reasoning providers include:

- OpenAI models
- Google Gemini models
- Local deterministic reasoning engine

The provider abstraction allows the core agent and tool architecture to remain independent from the underlying model provider.

This makes it easier to experiment with different models without redesigning the application.

---

# 🔧 AWS Tool Calling

CloudSage currently exposes four main AWS tools:

| Tool | Purpose |
|------|---------|
| `inspect_ec2` | Retrieves EC2 instances, states, types, availability zones and IP information |
| `explore_s3` | Lists S3 buckets and creation information |
| `get_cloudwatch_metrics` | Retrieves EC2 CPU utilization metrics |
| `analyze_cloud_cost` | Analyzes AWS spending and service-level costs |

### Example

User:

> "What EC2 instances are running?"

The flow is:

```text
User Query
    ↓
CloudSage Agent
    ↓
LLM determines required tool
    ↓
inspect_ec2
    ↓
AWS / Mock Data
    ↓
Structured Result
    ↓
LLM generates response
    ↓
User
```

This allows the assistant to convert natural-language requests into structured cloud operations.

---

# 📚 RAG — Cloud Knowledge Intelligence

CloudSage also includes a local Retrieval-Augmented Generation pipeline for AWS knowledge questions.

### RAG Pipeline

```text
AWS Knowledge Documents
          ↓
       Cleaning
          ↓
      Chunking
          ↓
      Embeddings
          ↓
    Vector Index
          ↓
   Similarity Search
          ↓
 Relevant Context
          ↓
    LLM Synthesis
          ↓
 Grounded Response
```

The knowledge base covers topics including:

- EC2
- S3
- CloudWatch
- IAM
- AWS Cost Management
- FinOps
- Cloud security
- Cloud monitoring
- Cost optimization

This allows CloudSage to handle both:

**Operational questions**

> "What EC2 instances are running?"

and

**Knowledge questions**

> "What is the difference between a security group and a network ACL?"

---

# 🔀 Hybrid AI Workflow

One of the main design ideas in CloudSage is combining **live cloud data** with **retrieved knowledge**.

```text
                         User Question
                               │
                               ▼
                       CloudSage Agent
                               │
              ┌────────────────┴────────────────┐
              │                                 │
              ▼                                 ▼
       Operational Query                  Knowledge Query
              │                                 │
              ▼                                 ▼
        AWS Tool Router                    RAG Retriever
              │                                 │
              ▼                                 ▼
        Live AWS Data                    AWS Knowledge
              │                                 │
              └────────────────┬────────────────┘
                               ▼
                        LLM Synthesis
                               │
                               ▼
                         Final Answer
```

This allows the system to use the right source for the right type of question.

---

# 🧪 Safe Mock / Sandbox Mode

CloudSage includes a development mock mode for safely testing the complete AI workflow without requiring live AWS operations.

When:

```env
AWS_MOCK_MODE=true
```

the AWS tools return realistic simulated responses.

When connected to AWS:

```env
AWS_MOCK_MODE=false
```

the tools communicate with AWS through Boto3.

### Why mock mode?

It allows developers to:

- Test the agent safely
- Demonstrate the application without AWS credentials
- Run automated tests without live cloud infrastructure
- Develop locally without risking real resources

---

# 🛡️ Security Design

CloudSage follows a least-privilege, read-only approach.

### Security principles

- 🔒 AWS operations are read-only
- 🔑 Credentials are loaded through environment/configuration
- 🚫 Credentials are never exposed to the frontend
- 🚫 The AI cannot directly access AWS credentials
- 🧪 Mock mode prevents accidental live AWS interaction during development
- 🛡️ Retrieved RAG content is treated as untrusted context
- 💻 Application runs locally on loopback by default

CloudSage is intentionally designed so that the AI assistant cannot create, modify, stop, or terminate AWS infrastructure.

---

# 🧠 Multi-Turn Context

CloudSage maintains lightweight in-memory session context.

For example:

**Turn 1**

> "What EC2 instances are running?"

**Turn 2**

> "Which one has the highest CPU?"

The system can use information from the previous turn and invoke the appropriate CloudWatch tool.

This allows more natural conversational interactions instead of treating every question as completely independent.

---

# 📊 Cost Intelligence

CloudSage can retrieve and analyze AWS Cost Explorer data.

Example:

> "How much am I spending on AWS?"

The assistant can return:

- Total estimated spend
- Currency
- Top cost driver
- Service-level cost breakdown

This gives the project a FinOps-oriented use case in addition to infrastructure monitoring.

---

# ✅ Testing & Evaluation

CloudSage includes an automated test suite covering:

- Unit tests
- Integration tests
- RAG behavior
- Agent behavior
- Tool-calling workflows
- API endpoints

Run the complete test suite with:

```bash
pytest tests/ -v
```

The current suite contains **45 automated tests** and is designed to run without external network dependencies.

---

# 🛠️ Tech Stack

### Backend

- Python
- FastAPI
- Boto3
- Pydantic

### AI

- LLM Provider Abstraction
- Tool Calling
- RAG
- Vector Search
- Embeddings
- Local Reasoning Engine

### Cloud

- AWS EC2
- AWS S3
- AWS CloudWatch
- AWS Cost Explorer
- AWS STS

### Testing

- Pytest
- Mock AWS responses
- Integration testing

### Frontend

- Web-based AI assistant interface

---

# 📁 Project Structure

```text
cloudsage/
│
├── app/
│   ├── ai/
│   │   ├── agent.py
│   │   ├── llm.py
│   │   └── tool_router.py
│   │
│   ├── tools/
│   │   ├── ec2.py
│   │   ├── s3.py
│   │   ├── cloudwatch.py
│   │   └── cost_explorer.py
│   │
│   ├── rag/
│   │   ├── documents.py
│   │   ├── ingest.py
│   │   └── retriever.py
│   │
│   └── routes/
│       └── chat.py
│
├── data/
├── frontend/
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

---

# 🚀 Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/shashi00007/cloudsage.git
cd cloudsage
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate it

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Copy:

```text
.env.example
```

to:

```text
.env
```

For safe local development, enable:

```env
AWS_MOCK_MODE=true
```

### 6. Build the RAG index

```bash
python -m app.rag.ingest
```

### 7. Start the application

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000/
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

---

# 🔮 Future Improvements

Potential next steps include:

- Standardized external tool integrations through MCP
- Expanded AI evaluation coverage
- Better observability and tracing
- Additional cloud providers
- More advanced FinOps recommendations
- Fine-grained authorization
- Production deployment
- Additional enterprise knowledge sources

---

# 🎯 Project Goal

CloudSage explores how LLMs can move beyond simple question-answering and become useful interfaces for real cloud operations.

The core design principle is:

> **Let the AI reason about the user's intent, give it controlled access to the right tools and knowledge, and evaluate the system before trusting it in real workflows.**

---

## 👨‍💻 Author

**Shashidhar S**

Computer Science (AI & Machine Learning)

Sahyadri College of Engineering and Management
```

### One important thing before you paste it

I intentionally changed the wording around **Claude**. Your current GitHub repository actually lists **OpenAI, Gemini, and a local reasoning engine** as the implemented providers. :chatgpt-content-reference{index="2"}

So don't put **“Claude-powered”** in the README unless you've actually added a Claude provider to the code.

However, your **resume says Claude and Claude Code are primary tools**, so if the interviewer asks about that, we need to prepare a clean, truthful explanation of exactly what you did. :chatgpt-content-reference{index="3"}

**This README will make the repo look much more professional without creating technical claims that the interviewer can catch you on.**
