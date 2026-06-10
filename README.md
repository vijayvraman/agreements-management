# Agreements Management

Legal agreements manager using multi-agent orchestration. Users can create, query, and modify legal agreements through a natural language interface backed by a hierarchy of AI agents.

---

## Architecture

```
User Request (HTTP POST /agreements/chat)
       │
       ▼
  Main FastAPI App  (port 8000)
       │
       ▼
  Planner Agent  [LangGraph StateGraph]
  - Classifies intent: create / query / modify
  - Routes to the appropriate specialist via A2A protocol
  - Synthesizes final response
       │
       │  A2A Protocol (HTTP JSON-RPC)
       ├─────────────────────┬─────────────────────┐
       ▼                     ▼                     ▼
Creator Agent          Query Agent          Modifier Agent
(port 8001)            (port 8002)          (port 8003)
[LangGraph]            [LangGraph]          [LangGraph]
[A2A Server]           [A2A Server]         [A2A Server]
       │
       │  MCP Protocol (stdio subprocess)
       ▼
  MCP Servers (shared by all specialists)
  ├── database_server.py   ← CRUD on agreements (SQLite)
  ├── template_server.py   ← Agreement templates & rendering
  └── document_server.py   ← PDF export / document import
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Agent framework | LangGraph |
| Agent-to-agent communication | A2A protocol (`a2a-sdk`) |
| Agent-to-tool communication | MCP protocol (`mcp`, `langchain-mcp-adapters`) |
| Planner LLM | Claude (`claude-sonnet-4-6`) via `langchain-anthropic` |
| Specialist LLM | Llama 3.1 8B Instant via Groq (`langchain-groq`) |
| API server | FastAPI + Uvicorn |
| Database | SQLAlchemy + SQLite (dev) |
| Observability | LangSmith (auto-traced) |

---

## Components

### Planner Agent
LangGraph `StateGraph` with three nodes:
1. **analyze_intent** — LLM classifies the request and extracts parameters
2. **route_to_specialist** — conditional edge selects creator / query / modifier
3. **synthesize_response** — formats the final user-facing answer

Communicates with specialist agents using the **Google A2A protocol** over HTTP.

### Specialist Agents (×3)
Each specialist is a standalone service running **Llama 3.1 8B Instant** via Groq:
- **LangGraph graph** — ReAct-style agent loop (agent node → tool node → agent node)
- **A2A server** — `A2AStarletteApplication` exposing `/.well-known/agent.json` and task endpoints
- **MCP client** — `MultiServerMCPClient` connects to the relevant MCP servers at startup

| Agent | Port | MCP tools available |
|---|---|---|
| Creator | 8001 | create_agreement, get_template, render_template, export_pdf |
| Query | 8002 | get_agreement, list_agreements, search_agreements, export_pdf |
| Modifier | 8003 | get/update/delete_agreement, render_template, export_pdf, import_doc |

### MCP Servers
Standalone `FastMCP` processes launched as stdio subprocesses by the specialist agents.

**database_server.py**
- `create_agreement(title, type, parties, content)`
- `get_agreement(id)`
- `list_agreements(status?, type?, party_name?)`
- `update_agreement(id, fields_to_update)`
- `search_agreements(query)` — full-text on title + content
- `delete_agreement(id)`

**template_server.py**
- `list_templates()` — available agreement types
- `get_template(type)` — raw template with `{{variable}}` placeholders
- `render_template(type, variables_dict)` — filled agreement text

**document_server.py**
- `export_to_pdf(agreement_id)` — returns base64-encoded PDF
- `import_document(content, format)` — extracts plain text

### Data Model

```
Agreement
├── id           UUID (primary key)
├── title        str
├── type         enum: NDA | ServiceAgreement | Employment | Other
├── parties      JSON list of {name, role}
├── content      text (agreement body)
├── status       enum: draft | active | expired | terminated
├── version      int (incremented on each update)
├── created_at   datetime
├── updated_at   datetime
└── metadata     JSON (arbitrary extra fields)
```

---

## Project Structure

```
agreements-management/
├── pyproject.toml
├── .env.example
├── src/
│   └── agreements/
│       ├── config.py                    # pydantic-settings
│       ├── models/agreement.py          # SQLAlchemy + Pydantic models
│       ├── database/session.py          # engine, session factory, init_db()
│       ├── mcp_servers/
│       │   ├── database_server.py
│       │   ├── template_server.py
│       │   └── document_server.py
│       ├── agents/
│       │   ├── planner/
│       │   │   ├── graph.py             # LangGraph StateGraph
│       │   │   └── prompts.py
│       │   ├── creator/
│       │   │   ├── graph.py
│       │   │   ├── executor.py          # A2A AgentExecutor
│       │   │   └── server.py            # A2AStarletteApplication
│       │   ├── query/
│       │   │   ├── graph.py
│       │   │   ├── executor.py
│       │   │   └── server.py
│       │   └── modifier/
│       │       ├── graph.py
│       │       ├── executor.py
│       │       └── server.py
│       ├── a2a/client.py                # Async A2A client (wraps a2a-sdk)
│       └── main.py                      # FastAPI entry point
├── tests/
│   ├── test_mcp_servers.py
│   ├── test_specialist_agents.py
│   └── test_planner.py
└── eval/                                # Harvey LAB-style evaluation suite
    ├── run_eval.py                      # CLI entry point
    ├── conftest.py                      # pytest fixtures for individual task debugging
    ├── tasks/
    │   ├── base.py                      # LABTask, LABRubric, LABEnvironment dataclasses
    │   ├── create_tasks.py              # 15 creation scenario tasks
    │   ├── query_tasks.py               # 12 query scenario tasks
    │   └── modify_tasks.py              # 10 modification scenario tasks
    ├── harness/
    │   ├── adapter.py                   # AgreementsAgentAdapter (mock + live modes)
    │   ├── runner.py                    # Sequential TaskRunner with DB isolation
    │   └── mock_backend.py              # Inline LangChain tools + specialist graph dispatch
    ├── evaluator/
    │   ├── judge.py                     # LLMJudge — batched rubric scoring via Claude
    │   └── prompts.py                   # RUBRIC_EVALUATION_PROMPT
    └── metrics/
        └── reporter.py                  # MetricsReporter, EvalSummary
```

---

## Setup

### 1. Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Configure environment
```bash
cp .env.example .env
# Fill in:
#   ANTHROPIC_API_KEY       — planner agent (Claude)
#   GROQ_API_KEY            — specialist agents (Llama 3.1 8B via Groq)
#   LANGSMITH_API_KEY
#   LANGSMITH_PROJECT=agreements-management
#   LANGSMITH_TRACING=true
```

### 3. Start services
```bash
# Specialist agents (each in a separate terminal)
uvicorn agreements.agents.creator.server:app --port 8001
uvicorn agreements.agents.query.server:app  --port 8002
uvicorn agreements.agents.modifier.server:app --port 8003

# Main API + planner
uvicorn agreements.main:app --port 8000
```

---

## Usage

```bash
# Create an agreement
curl -X POST http://localhost:8000/agreements/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Create an NDA between Acme Corp and Beta Ltd, effective today"}'

# Query agreements
curl -X POST http://localhost:8000/agreements/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me all active agreements involving Acme Corp"}'

# Modify an agreement
curl -X POST http://localhost:8000/agreements/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Update agreement abc-123: change status to expired"}'
```

---

## Evaluation

Harvey LAB-style evaluation pipeline that measures agent quality using structured tasks, expert-written binary rubrics, and an LLM-as-judge scorer. The primary metric is **all-pass rate** — a task passes only when every required rubric passes, mirroring high-stakes legal review.

37 tasks across three intents (15 create, 12 query, 10 modify). The LLM judge (Claude Sonnet 4.6) evaluates all rubrics for a task in a single batched call.

### Run (no servers needed)

```bash
# Install eval dependency
pip install -e ".[eval]"

# Quick check — creation tasks only
python eval/run_eval.py --mode mock --intent create

# Full evaluation with JSON report
python eval/run_eval.py --mode mock --output eval_results.json

# Filter by intent
python eval/run_eval.py --mode mock --intent query
python eval/run_eval.py --mode mock --intent modify

# Stop after first failure
python eval/run_eval.py --mode mock --fail-fast

# Use a stronger judge model
python eval/run_eval.py --mode mock --verifier-model claude-opus-4-8
```

### Run against live servers

```bash
# Start all 4 servers first, then:
python eval/run_eval.py --mode live --output eval_live.json
```

### Debug a single task

```bash
pytest eval/ -k "create_nda_complete_001" -v
```

### Output

The console prints a per-task rubric breakdown followed by a summary table:

```
  [ALL-PASS] create_nda_complete_001
    ✓ r1: The response explicitly names Acme Corp.
    ✓ r2: Beta Ltd appears in the response.
    ...

  AGREEMENTS AGENT EVALUATION — Harvey LAB-style Report
  ============================================================
  Total tasks:        37
  All-pass (primary): 28/37  (75.7%)
  Partial-pass:        7/37  (18.9%)
  Zero-pass:           2
  Errors:              0
  Mean latency:      4823ms
  P95 latency:       9201ms

  By intent:
    create      all-pass=80.0%  (12/15)  errors=0
    modify      all-pass=70.0%   (7/10)  errors=0
    query       all-pass=75.0%   (9/12)  errors=0
  ============================================================
```

---

## Observability

All LangGraph nodes are automatically traced to LangSmith when `LANGSMITH_TRACING=true` is set. View traces at [smith.langchain.com](https://smith.langchain.com) under the `agreements-management` project to see the full planner → specialist → MCP tool call chain.











