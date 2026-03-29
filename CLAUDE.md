# CLAUDE.md — TradingAgents (leokeechye fork)

## Project Overview
Multi-agent LLM trading framework (forked from TauricResearch/TradingAgents).
Deployed on Railway at: tradingagents-production-c147.up.railway.app

## Key Directories
- `cli/` — Current CLI interface
- `tradingagents/` — Core framework (agents, graph, config)
- `tradingagents/graph/trading_graph.py` — TradingAgentsGraph main class
- `tradingagents/default_config.py` — DEFAULT_CONFIG
- `main.py` — Entry point

## Core Usage Pattern
```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
ta = TradingAgentsGraph(debug=True, config=DEFAULT_CONFIG.copy())
_, decision = ta.propagate("NVDA", "2026-01-15")
```

## Stack
- Python, LangGraph, multiple LLM providers
- Deployed via Railway (Docker)
- Currently CLI-only, migrating to web GUI

## Setup & Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the CLI
python -m cli.main

# Run programmatically (see main.py for example)
python main.py

# Run basic validation tests
python test.py
```

**Python version:** >= 3.10. Build system uses setuptools via `pyproject.toml`.

**Environment variables** (set in shell or `.env` from `.env.example`):
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `XAI_API_KEY`, `OPENROUTER_API_KEY` — LLM providers
- `ALPHA_VANTAGE_API_KEY` — optional alternative data source (default is Yahoo Finance, no key needed)

## Rules
- Always run tests after changes
- Keep Railway deployment compatible (Dockerfile/Procfile)
- Don't break the existing CLI — add GUI alongside it

## Architecture

### Pipeline Phases

The system runs as a LangGraph `StateGraph` with four sequential phases:

1. **Analyst Phase** — Specialized analysts (market/sentiment/news/fundamentals) each call data tools in a loop, producing reports stored in `AgentState`
2. **Research Debate Phase** — Bull and bear researchers debate for `max_debate_rounds` cycles, then a research manager judges and outputs an investment plan (BUY/SELL/HOLD)
3. **Trader Phase** — Creates a concrete trading proposal from the investment plan and all analyst reports
4. **Risk Debate Phase** — Aggressive/neutral/conservative risk analysts debate for `max_risk_discuss_rounds` cycles, then a risk manager produces the final trade decision

### Key Components

- **`tradingagents/graph/trading_graph.py`** — `TradingAgentsGraph`: main orchestrator. Call `propagate(ticker, date)` to run the pipeline, `reflect_and_remember()` to learn from outcomes.
- **`tradingagents/graph/setup.py`** — Constructs the LangGraph `StateGraph` with conditional edges controlling tool loops and debate cycles.
- **`tradingagents/graph/conditional_logic.py`** — Routing functions that control when analysts stop calling tools and when debates end.
- **`tradingagents/agents/utils/agent_states.py`** — Three `TypedDict` state classes: `AgentState`, `InvestDebateState`, `RiskDebateState`.
- **`tradingagents/default_config.py`** — `DEFAULT_CONFIG` dict with LLM provider, model names, debate rounds, and data vendor routing.
- **`tradingagents/llm_clients/factory.py`** — `create_llm_client()` factory supporting OpenAI, Anthropic, Google, xAI, OpenRouter, Ollama.
- **`tradingagents/dataflows/interface.py`** — Routes data tool calls to the configured vendor (Yahoo Finance or Alpha Vantage).
- **`tradingagents/agents/utils/memory.py`** — BM25-based experience memory (no API calls). Stores per-agent (situation, recommendation) pairs for reflection/learning.

### Agent Roles

| Directory | Agents | Purpose |
|-----------|--------|---------|
| `agents/analysts/` | market, fundamentals, news, social_media | Gather and analyze data via tool calls |
| `agents/researchers/` | bull, bear | Debate investment merits |
| `agents/managers/` | research_manager, risk_manager | Judge debates, make decisions |
| `agents/risk_mgmt/` | aggressive, neutral, conservative | Debate risk tolerance |
| `agents/trader/` | trader | Create trading plan |

### Data Flow

Analysts use tools defined in `agents/utils/` (`core_stock_tools.py`, `technical_indicators_tools.py`, `fundamental_data_tools.py`, `news_data_tools.py`). These tools call through `dataflows/interface.py` which routes to the configured vendor implementation (`y_finance.py` or `alpha_vantage.py`). Data is cached in `dataflows/data_cache/`.

### Configuration

The config dict in `default_config.py` controls:
- `llm_provider` / `deep_think_llm` / `quick_think_llm` — which LLM to use
- `max_debate_rounds` / `max_risk_discuss_rounds` — debate cycle counts
- `data_vendors` — per-category data source routing (yfinance vs alpha_vantage)
- `tool_vendors` — per-tool overrides for data source

### CLI

`cli/main.py` uses Typer + Rich + Questionary for interactive ticker/date/model selection and progress display.

### Output

Results are saved as JSON to `eval_results/{ticker}/TradingAgentsStrategy_logs/full_states_log_{date}.json`.
