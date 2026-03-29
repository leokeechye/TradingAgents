"""
TradingAgents — Streamlit Web GUI
Multi-agent LLM-powered trading analysis framework.
"""

import os
import sys
import time
import datetime
import threading
import json
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="TradingAgents",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Model options (mirrored from cli/utils.py)
# ---------------------------------------------------------------------------
PROVIDERS = {
    "OpenAI": {
        "url": "https://api.openai.com/v1",
        "env_key": "OPENAI_API_KEY",
        "quick_models": [
            ("GPT-5 Mini", "gpt-5-mini"),
            ("GPT-5 Nano", "gpt-5-nano"),
            ("GPT-5.2", "gpt-5.2"),
            ("GPT-5.1", "gpt-5.1"),
            ("GPT-4.1", "gpt-4.1"),
        ],
        "deep_models": [
            ("GPT-5.2", "gpt-5.2"),
            ("GPT-5.1", "gpt-5.1"),
            ("GPT-5", "gpt-5"),
            ("GPT-4.1", "gpt-4.1"),
            ("GPT-5 Mini", "gpt-5-mini"),
            ("GPT-5 Nano", "gpt-5-nano"),
        ],
    },
    "Anthropic": {
        "url": "https://api.anthropic.com/",
        "env_key": "ANTHROPIC_API_KEY",
        "quick_models": [
            ("Claude Haiku 4.5", "claude-haiku-4-5"),
            ("Claude Sonnet 4.5", "claude-sonnet-4-5"),
            ("Claude Sonnet 4", "claude-sonnet-4-20250514"),
        ],
        "deep_models": [
            ("Claude Sonnet 4.5", "claude-sonnet-4-5"),
            ("Claude Opus 4.5", "claude-opus-4-5"),
            ("Claude Opus 4.1", "claude-opus-4-1-20250805"),
            ("Claude Haiku 4.5", "claude-haiku-4-5"),
            ("Claude Sonnet 4", "claude-sonnet-4-20250514"),
        ],
    },
    "Google": {
        "url": "https://generativelanguage.googleapis.com/v1",
        "env_key": "GOOGLE_API_KEY",
        "quick_models": [
            ("Gemini 3 Flash", "gemini-3-flash-preview"),
            ("Gemini 2.5 Flash", "gemini-2.5-flash"),
            ("Gemini 3 Pro", "gemini-3-pro-preview"),
            ("Gemini 2.5 Flash Lite", "gemini-2.5-flash-lite"),
        ],
        "deep_models": [
            ("Gemini 3 Pro", "gemini-3-pro-preview"),
            ("Gemini 3 Flash", "gemini-3-flash-preview"),
            ("Gemini 2.5 Flash", "gemini-2.5-flash"),
        ],
    },
    "xAI": {
        "url": "https://api.x.ai/v1",
        "env_key": "XAI_API_KEY",
        "quick_models": [
            ("Grok 4.1 Fast (Non-Reasoning)", "grok-4-1-fast-non-reasoning"),
            ("Grok 4 Fast (Non-Reasoning)", "grok-4-fast-non-reasoning"),
            ("Grok 4.1 Fast (Reasoning)", "grok-4-1-fast-reasoning"),
            ("Grok 4 Fast (Reasoning)", "grok-4-fast-reasoning"),
        ],
        "deep_models": [
            ("Grok 4.1 Fast (Reasoning)", "grok-4-1-fast-reasoning"),
            ("Grok 4 Fast (Reasoning)", "grok-4-fast-reasoning"),
            ("Grok 4", "grok-4-0709"),
            ("Grok 4.1 Fast (Non-Reasoning)", "grok-4-1-fast-non-reasoning"),
            ("Grok 4 Fast (Non-Reasoning)", "grok-4-fast-non-reasoning"),
        ],
    },
    "OpenRouter": {
        "url": "https://openrouter.ai/api/v1",
        "env_key": "OPENROUTER_API_KEY",
        "quick_models": [
            ("NVIDIA Nemotron 3 Nano 30B (free)", "nvidia/nemotron-3-nano-30b-a3b:free"),
            ("Z.AI GLM 4.5 Air (free)", "z-ai/glm-4.5-air:free"),
        ],
        "deep_models": [
            ("Z.AI GLM 4.5 Air (free)", "z-ai/glm-4.5-air:free"),
            ("NVIDIA Nemotron 3 Nano 30B (free)", "nvidia/nemotron-3-nano-30b-a3b:free"),
        ],
    },
    "Ollama": {
        "url": "http://localhost:11434/v1",
        "env_key": "OLLAMA_API_KEY",
        "quick_models": [
            ("Qwen3:latest (8B)", "qwen3:latest"),
            ("GPT-OSS:latest (20B)", "gpt-oss:latest"),
            ("GLM-4.7-Flash:latest (30B)", "glm-4.7-flash:latest"),
        ],
        "deep_models": [
            ("GLM-4.7-Flash:latest (30B)", "glm-4.7-flash:latest"),
            ("GPT-OSS:latest (20B)", "gpt-oss:latest"),
            ("Qwen3:latest (8B)", "qwen3:latest"),
        ],
    },
}

ANALYST_OPTIONS = {
    "Market Analyst": "market",
    "Social Media Analyst": "social",
    "News Analyst": "news",
    "Fundamentals Analyst": "fundamentals",
}

DEPTH_OPTIONS = {
    "Shallow — Quick analysis, 1 debate round": 1,
    "Medium — Moderate depth, 3 debate rounds": 3,
    "Deep — Comprehensive, 5 debate rounds": 5,
}

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Tighter spacing */
    .block-container { padding-top: 1.5rem; }
    /* Status badges */
    .status-pending { color: #fbbf24; }
    .status-running { color: #3b82f6; }
    .status-done    { color: #22c55e; }
    .status-error   { color: #ef4444; }
    /* Report cards */
    .report-card {
        background: #1e1e2e;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        border-left: 3px solid #6366f1;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar — Configuration
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("📊 TradingAgents")
    st.caption("Multi-Agent LLM Trading Analysis")
    st.divider()

    # Ticker
    ticker = st.text_input("Ticker Symbol", value="SPY", max_chars=10).strip().upper()

    # Date
    analysis_date = st.date_input(
        "Analysis Date",
        value=datetime.date.today(),
        max_value=datetime.date.today(),
    )

    st.divider()

    # Analysts
    st.subheader("Analyst Team")
    selected_analysts = []
    for display_name, key in ANALYST_OPTIONS.items():
        if st.checkbox(display_name, value=True, key=f"analyst_{key}"):
            selected_analysts.append(key)

    st.divider()

    # Research depth
    depth_label = st.selectbox("Research Depth", list(DEPTH_OPTIONS.keys()))
    debate_rounds = DEPTH_OPTIONS[depth_label]

    st.divider()

    # LLM Provider
    st.subheader("LLM Configuration")
    provider_name = st.selectbox("Provider", list(PROVIDERS.keys()))
    provider_info = PROVIDERS[provider_name]

    # Model selectors
    quick_labels = [m[0] for m in provider_info["quick_models"]]
    deep_labels = [m[0] for m in provider_info["deep_models"]]

    quick_idx = st.selectbox("Quick-Thinking Model", range(len(quick_labels)),
                             format_func=lambda i: quick_labels[i])
    deep_idx = st.selectbox("Deep-Thinking Model", range(len(deep_labels)),
                            format_func=lambda i: deep_labels[i])

    quick_model = provider_info["quick_models"][quick_idx][1]
    deep_model = provider_info["deep_models"][deep_idx][1]

    # Provider-specific options
    openai_reasoning = None
    google_thinking = None
    if provider_name == "OpenAI":
        openai_reasoning = st.selectbox(
            "Reasoning Effort", ["medium", "high", "low"], index=0
        )
    elif provider_name == "Google":
        google_thinking = st.selectbox(
            "Thinking Mode", ["high", "minimal"], index=0
        )

    # API key status
    env_key = provider_info["env_key"]
    has_key = bool(os.environ.get(env_key))
    if has_key:
        st.success(f"{env_key} detected", icon="✅")
    else:
        st.warning(f"{env_key} not set", icon="⚠️")

    st.divider()
    st.caption("For research purposes only. Not financial advice.")


# ---------------------------------------------------------------------------
# Helper: build config dict
# ---------------------------------------------------------------------------
def build_config():
    from tradingagents.default_config import DEFAULT_CONFIG
    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = provider_name.lower()
    config["backend_url"] = provider_info["url"]
    config["quick_think_llm"] = quick_model
    config["deep_think_llm"] = deep_model
    config["max_debate_rounds"] = debate_rounds
    config["max_risk_discuss_rounds"] = debate_rounds
    if openai_reasoning:
        config["openai_reasoning_effort"] = openai_reasoning
    if google_thinking:
        config["google_thinking_level"] = google_thinking
    return config


# ---------------------------------------------------------------------------
# Helper: extract reports from final_state
# ---------------------------------------------------------------------------
def extract_reports(final_state):
    """Return an ordered list of (section_title, subsections) from final state."""
    sections = []

    # I. Analyst Reports
    analyst_parts = []
    if final_state.get("market_report"):
        analyst_parts.append(("Market Analyst", final_state["market_report"]))
    if final_state.get("sentiment_report"):
        analyst_parts.append(("Social Media Analyst", final_state["sentiment_report"]))
    if final_state.get("news_report"):
        analyst_parts.append(("News Analyst", final_state["news_report"]))
    if final_state.get("fundamentals_report"):
        analyst_parts.append(("Fundamentals Analyst", final_state["fundamentals_report"]))
    if analyst_parts:
        sections.append(("I. Analyst Team Reports", analyst_parts))

    # II. Research Debate
    debate = final_state.get("investment_debate_state", {})
    research_parts = []
    if debate.get("bull_history"):
        research_parts.append(("Bull Researcher", debate["bull_history"]))
    if debate.get("bear_history"):
        research_parts.append(("Bear Researcher", debate["bear_history"]))
    if debate.get("judge_decision"):
        research_parts.append(("Research Manager", debate["judge_decision"]))
    if research_parts:
        sections.append(("II. Research Team Decision", research_parts))

    # III. Trader
    if final_state.get("trader_investment_plan"):
        sections.append(("III. Trading Plan", [
            ("Trader", final_state["trader_investment_plan"])
        ]))

    # IV. Risk Management
    risk = final_state.get("risk_debate_state", {})
    risk_parts = []
    if risk.get("aggressive_history"):
        risk_parts.append(("Aggressive Analyst", risk["aggressive_history"]))
    if risk.get("conservative_history"):
        risk_parts.append(("Conservative Analyst", risk["conservative_history"]))
    if risk.get("neutral_history"):
        risk_parts.append(("Neutral Analyst", risk["neutral_history"]))
    if risk_parts:
        sections.append(("IV. Risk Management", risk_parts))

    # V. Portfolio Manager
    if risk.get("judge_decision"):
        sections.append(("V. Portfolio Manager Decision", [
            ("Portfolio Manager", risk["judge_decision"])
        ]))

    return sections


# ---------------------------------------------------------------------------
# Helper: save report to disk (replicates CLI behavior)
# ---------------------------------------------------------------------------
def save_report(final_state, ticker_symbol, trade_date):
    """Save report files and return the path to the complete report."""
    results_dir = os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results")
    save_path = Path(results_dir) / ticker_symbol / str(trade_date)
    save_path.mkdir(parents=True, exist_ok=True)

    sections = extract_reports(final_state)
    md_parts = []
    for section_title, subsections in sections:
        content = "\n\n".join(f"### {name}\n{text}" for name, text in subsections)
        md_parts.append(f"## {section_title}\n\n{content}")

    header = (
        f"# Trading Analysis Report: {ticker_symbol}\n\n"
        f"Date: {trade_date}\n"
        f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    )
    report_text = header + "\n\n".join(md_parts)
    report_file = save_path / "complete_report.md"
    report_file.write_text(report_text)
    return report_file


# ---------------------------------------------------------------------------
# Agent status labels for progress tracking
# ---------------------------------------------------------------------------
AGENT_PIPELINE = [
    ("Analyst Team", []),       # filled dynamically
    ("Research Team", ["Bull Researcher", "Bear Researcher", "Research Manager"]),
    ("Trading Team", ["Trader"]),
    ("Risk Management", ["Aggressive Analyst", "Conservative Analyst", "Neutral Analyst"]),
    ("Portfolio", ["Portfolio Manager"]),
]

ANALYST_AGENT_NAMES = {
    "market": "Market Analyst",
    "social": "Social Media Analyst",
    "news": "News Analyst",
    "fundamentals": "Fundamentals Analyst",
}

ANALYST_REPORT_MAP = {
    "market": "market_report",
    "social": "sentiment_report",
    "news": "news_report",
    "fundamentals": "fundamentals_report",
}


# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.header(f"Analysis: {ticker}")

if not selected_analysts:
    st.error("Select at least one analyst in the sidebar.")
    st.stop()

# Run button
run_clicked = st.button("🚀 Run Analysis", type="primary", use_container_width=True)

if run_clicked:
    config = build_config()
    date_str = analysis_date.strftime("%Y-%m-%d")

    # Progress placeholders
    status_container = st.status(f"Analyzing **{ticker}** for {date_str}...", expanded=True)
    progress_bar = st.progress(0)
    stats_placeholder = st.empty()

    # Dynamically build analyst agent list
    analyst_agents = [ANALYST_AGENT_NAMES[a] for a in selected_analysts]
    all_agents = (
        analyst_agents
        + ["Bull Researcher", "Bear Researcher", "Research Manager"]
        + ["Trader"]
        + ["Aggressive Analyst", "Conservative Analyst", "Neutral Analyst"]
        + ["Portfolio Manager"]
    )
    total_agents = len(all_agents)
    completed_agents = set()

    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from cli.stats_handler import StatsCallbackHandler

        stats_handler = StatsCallbackHandler()

        with status_container:
            st.write("Initializing agents...")

            graph = TradingAgentsGraph(
                selected_analysts=selected_analysts,
                config=config,
                callbacks=[stats_handler],
            )

            # Build initial state and args
            init_state = graph.propagator.create_initial_state(ticker, date_str)
            args = graph.propagator.get_graph_args()

            # --- Stream through the graph ---
            st.write("Running agent pipeline...")

            final_state = None
            for chunk in graph.graph.stream(init_state, **args):
                final_state = chunk

                # Track analyst completion
                for analyst_key in selected_analysts:
                    report_key = ANALYST_REPORT_MAP[analyst_key]
                    if chunk.get(report_key):
                        agent_name = ANALYST_AGENT_NAMES[analyst_key]
                        if agent_name not in completed_agents:
                            completed_agents.add(agent_name)
                            st.write(f"✅ {agent_name} complete")

                # Track research debate
                debate = chunk.get("investment_debate_state", {})
                if debate.get("bull_history") and "Bull Researcher" not in completed_agents:
                    completed_agents.add("Bull Researcher")
                    st.write("✅ Bull Researcher complete")
                if debate.get("bear_history") and "Bear Researcher" not in completed_agents:
                    completed_agents.add("Bear Researcher")
                    st.write("✅ Bear Researcher complete")
                if debate.get("judge_decision") and "Research Manager" not in completed_agents:
                    completed_agents.add("Research Manager")
                    st.write("✅ Research Manager complete")

                # Track trader
                if chunk.get("trader_investment_plan") and "Trader" not in completed_agents:
                    completed_agents.add("Trader")
                    st.write("✅ Trader complete")

                # Track risk debate
                risk = chunk.get("risk_debate_state", {})
                if risk.get("aggressive_history") and "Aggressive Analyst" not in completed_agents:
                    completed_agents.add("Aggressive Analyst")
                    st.write("✅ Aggressive Analyst complete")
                if risk.get("conservative_history") and "Conservative Analyst" not in completed_agents:
                    completed_agents.add("Conservative Analyst")
                    st.write("✅ Conservative Analyst complete")
                if risk.get("neutral_history") and "Neutral Analyst" not in completed_agents:
                    completed_agents.add("Neutral Analyst")
                    st.write("✅ Neutral Analyst complete")
                if risk.get("judge_decision") and "Portfolio Manager" not in completed_agents:
                    completed_agents.add("Portfolio Manager")
                    st.write("✅ Portfolio Manager complete")

                # Update progress
                progress = len(completed_agents) / total_agents
                progress_bar.progress(progress)

                # Update stats
                stats = stats_handler.get_stats()
                stats_placeholder.markdown(
                    f"**LLM calls:** {stats['llm_calls']} · "
                    f"**Tool calls:** {stats['tool_calls']} · "
                    f"**Tokens in:** {stats['tokens_in']:,} · "
                    f"**Tokens out:** {stats['tokens_out']:,}"
                )

        # Store state for reflection
        graph.curr_state = final_state
        graph._log_state(date_str, final_state)

        progress_bar.progress(1.0)
        status_container.update(label="Analysis complete!", state="complete", expanded=False)

        # Save report
        report_path = save_report(final_state, ticker, date_str)

        # ----- Display results -----
        st.divider()
        st.subheader("Results")

        # Final decision highlight
        final_decision = final_state.get("final_trade_decision", "")
        if final_decision:
            # Try to extract BUY/SELL/HOLD signal
            decision_upper = final_decision.upper()
            if "BUY" in decision_upper:
                st.success("Signal: **BUY**", icon="📈")
            elif "SELL" in decision_upper:
                st.error("Signal: **SELL**", icon="📉")
            elif "HOLD" in decision_upper:
                st.info("Signal: **HOLD**", icon="⏸️")

        # Display all report sections in tabs
        sections = extract_reports(final_state)
        if sections:
            tab_names = [s[0] for s in sections]
            tabs = st.tabs(tab_names)
            for tab, (section_title, subsections) in zip(tabs, sections):
                with tab:
                    for name, content in subsections:
                        with st.expander(name, expanded=True):
                            st.markdown(content)

        # Download button
        if report_path.exists():
            report_text = report_path.read_text()
            st.download_button(
                "📥 Download Full Report",
                data=report_text,
                file_name=f"{ticker}_{date_str}_report.md",
                mime="text/markdown",
            )

        # Final stats
        stats = stats_handler.get_stats()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("LLM Calls", stats["llm_calls"])
        col2.metric("Tool Calls", stats["tool_calls"])
        col3.metric("Tokens In", f"{stats['tokens_in']:,}")
        col4.metric("Tokens Out", f"{stats['tokens_out']:,}")

    except Exception as e:
        status_container.update(label="Analysis failed", state="error")
        st.error(f"Error: {e}")
        st.exception(e)

# Show previous results if no run in progress
elif not run_clicked:
    st.info("Configure your analysis in the sidebar and click **Run Analysis** to begin.")

    # Show any existing reports
    results_dir = Path(os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"))
    if results_dir.exists():
        reports = sorted(results_dir.glob("**/complete_report.md"), reverse=True)
        if reports:
            st.subheader("Previous Reports")
            for report_file in reports[:10]:
                parts = report_file.parts
                label = " / ".join(parts[-3:-1])  # ticker / date
                with st.expander(label):
                    st.markdown(report_file.read_text())
