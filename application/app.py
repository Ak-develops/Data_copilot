"""Streamlit chat frontend — interactive web dashboard."""

from __future__ import annotations

import time
import requests
import streamlit as st

from config import settings
from logger import (
    generate_id,
    get_logger,
    reset_request_context,
    set_request_context,
    setup_logging,
    truncate_payload,
)

setup_logging(settings.log_level)
logger = get_logger(__name__)

st.set_page_config(
    page_title="Stock Agent Chat",
    page_icon="📊",
    layout="wide",
)

if "session_id" not in st.session_state:
    st.session_state["session_id"] = generate_id("sess-")
    logger.info("Initialized new Streamlit session | session_id=%s", st.session_state["session_id"])

API_BASE = "http://localhost:8000"

TOOL_ICONS = {
    "get_stock_price": "💰",
    "compare_returns": "📊",
    "plot_stock_trend": "📈",
    "plot_comparison": "📉",
    "compare_multiple": "🔀",
}
TOOL_EXAMPLE_QUERIES = {
    "get_stock_price": "What is the latest price of TCS?",
    "compare_returns": "Compare the returns of TCS and Reliance for 2023",
    "plot_stock_trend": "Plot the stock trend of Infosys from 2023 to 2024",
    "plot_comparison": "Compare TCS and Infosys for 2023 in form of a graph",
    "compare_multiple": "Compare TCS, Infosys, Wipro and HCL Tech for the year 2023",
}

# Tool parameter definitions for display in Interface Library
TOOL_SIGNATURES = {
    "get_stock_price": {
        "signature": "get_stock_price(ticker: str) -> dict",
        "params": {"ticker": "Stock ticker with .NS suffix (e.g. TCS.NS)"},
        "returns": "Latest close, open, high, low, volume, date",
    },
    "compare_returns": {
        "signature": "compare_returns(ticker1: str, ticker2: str, start: str, end: str) -> dict",
        "params": {
            "ticker1": "First stock ticker",
            "ticker2": "Second stock ticker",
            "start": "Start date YYYY-MM-DD",
            "end": "End date YYYY-MM-DD",
        },
        "returns": "Return % for both stocks, winner declaration",
    },
    "plot_stock_trend": {
        "signature": "plot_stock_trend(ticker: str, start: str, end: str) -> dict",
        "params": {
            "ticker": "Stock ticker",
            "start": "Start date YYYY-MM-DD",
            "end": "End date YYYY-MM-DD",
        },
        "returns": "Chart PNG path, min/max/avg close",
    },
    "plot_comparison": {
        "signature": "plot_comparison(ticker1: str, ticker2: str, start: str, end: str) -> dict",
        "params": {
            "ticker1": "First stock ticker",
            "ticker2": "Second stock ticker",
            "start": "Start date YYYY-MM-DD",
            "end": "End date YYYY-MM-DD",
        },
        "returns": "Dual-line normalised chart PNG, return % for both",
    },
    "compare_multiple": {
        "signature": "compare_multiple(tickers: list[str], start: str, end: str) -> dict",
        "params": {
            "tickers": "List of 2-5 stock tickers",
            "start": "Start date YYYY-MM-DD",
            "end": "End date YYYY-MM-DD",
        },
        "returns": "Multi-line chart + ranked bar chart PNG, all return %",
    },
}


# ── Helpers ──────────────────────────────────────────────────────────

def get_history() -> list[dict[str, str]]:
    return [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.get("messages", [])[-6:]
    ]


def call_api_and_render(prompt: str) -> None:
    session_id = st.session_state.get("session_id", "-")
    req_id = generate_id("req-")
    tokens = set_request_context(request_id=req_id, session_id=session_id)
    req_start = time.perf_counter()

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                agent_mode = st.session_state.get("agent_mode", "interface")
                routing_mode = st.session_state.get("routing_mode", "vector")

                # Choose endpoint based on mode
                if agent_mode == "interface":
                    endpoint = f"{API_BASE}/api/chat"
                else:
                    endpoint = f"{API_BASE}/api/chat/baseline"

                logger.info(
                    "UI sending query | mode=%s | routing=%s | endpoint=%s | query=%s",
                    agent_mode,
                    routing_mode,
                    endpoint,
                    truncate_payload(prompt, 500),
                )

                resp = requests.post(
                    endpoint,
                    json={
                        "query": prompt,
                        "routing_mode": routing_mode,
                        "history": get_history(),
                    },
                    headers={
                        "X-Request-ID": req_id,
                        "X-Session-ID": session_id,
                    },
                    timeout=60,
                )
                ui_latency_ms = (time.perf_counter() - req_start) * 1000
                if resp.ok:
                    data = resp.json()
                    logger.info(
                        "UI received response | status=%d | tool=%s | api_latency=%.1fms | ui_latency=%.1fms",
                        resp.status_code,
                        data.get("tool_used"),
                        data.get("latency_ms", 0.0),
                        ui_latency_ms,
                    )
                    st.markdown(data["answer"])
                    
                    # Display chart if available
                    chart_path = data.get("chart_path")
                    if chart_path:
                        # Convert Path to string if needed and ensure it exists
                        chart_path_str = str(chart_path)
                        try:
                            st.image(chart_path_str)
                        except Exception as e:
                            logger.warning("Failed to render chart %s: %s", chart_path_str, e)
                            st.error(f"Could not load chart: {e}")
                            st.caption(f"Chart path: {chart_path_str}")

                    from_hist = data.get("args_from_history") or []
                    args = data.get("tool_args") or {}
                    if from_hist:
                        st.caption(
                            f"Tool: `{data.get('tool_used', 'N/A')}` | "
                            f"Args: `{args}` | "
                            f"From history: `{from_hist}` | "
                            f"Latency: {data['latency_ms']:.0f}ms"
                        )
                    else:
                        st.caption(
                            f"Tool: `{data.get('tool_used', 'N/A')}` | "
                            f"Args: `{args}` | "
                            f"Latency: {data['latency_ms']:.0f}ms"
                        )

                    # Store in session for Interface Library tab
                    if "interface_log" not in st.session_state:
                        st.session_state.interface_log = []
                    st.session_state.interface_log.append({
                        "query": prompt,
                        "tool": data.get("tool_used"),
                        "args": args,
                        "args_from_history": from_hist,
                        "latency_ms": data["latency_ms"],
                        "is_new": data.get("is_new_interface", False),
                        "token_usage": data.get("token_usage", 0),
                        "mode": agent_mode,
                    })

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": data["answer"],
                        "tool": data.get("tool_used"),
                        "args": args,
                        "args_from_history": from_hist,
                        "latency": data["latency_ms"],
                        "chart": data.get("chart_path"),
                    })
                else:
                    logger.error(
                        "API error response | status=%d | body=%s",
                        resp.status_code,
                        truncate_payload(resp.text, 500),
                    )
                    st.error(f"API error: {resp.status_code} — {resp.text}")
            except requests.RequestException as e:
                logger.exception("Could not reach API server: %s", e)
                st.error(f"Could not reach API server: {e}")
            finally:
                reset_request_context(tokens)


# ── Sidebar ───────────────────────────────────────────────────────────
st.sidebar.title("⚙️ Control Panel")

# ── Mode Selection ─────────────────────────────────────────────────────
st.sidebar.subheader("🤖 Agent Mode")
agent_mode = st.sidebar.radio(
    "Select Mode",
    options=["interface", "baseline"],
    format_func=lambda x: "Interface Agent (with reuse)" if x == "interface" else "General LLM (no reuse)",
    index=0,
    help="Interface Agent reuses existing interfaces. General LLM generates fresh code every time."
)
st.session_state["agent_mode"] = agent_mode

if agent_mode == "interface":
    st.sidebar.success("✅ Using Interface Agent - reuses existing tools")
else:
    st.sidebar.warning("⚠️ Using General LLM - no interface reuse")

st.sidebar.divider()

routing_mode = st.sidebar.radio(
    "Routing Mode",
    options=["vector", "naive"],
    index=0,
    help="Vector RAG retrieves top-k tools via embeddings. Naive includes all tools in the prompt.",
)
st.session_state["routing_mode"] = routing_mode

st.sidebar.divider()

# ── Reset Button ──────────────────────────────────────────────────────
st.sidebar.subheader("🔄 Reset System")
st.sidebar.markdown("Clear conversation history and delete all registered interfaces.")

if st.sidebar.button("🗑️ Reset Chat & Interfaces", type="primary", use_container_width=True):
    session_id = st.session_state.get("session_id", "-")
    tokens = set_request_context(request_id=generate_id("req-"), session_id=session_id)
    try:
        logger.info("UI reset triggered")
        # Clear session state (conversation + interface log)
        st.session_state.messages = []
        st.session_state.interface_log = []
        
        # Delete all interfaces from backend
        response = requests.post(
            f"{API_BASE}/api/reset",
            headers={"X-Session-ID": session_id},
            timeout=10,
        )
        
        if response.ok:
            logger.info("UI reset succeeded")
            st.sidebar.success("✅ System reset successfully!")
            st.sidebar.info("All interfaces deleted. Chat history cleared.")
            time.sleep(1)
            st.rerun()
        else:
            logger.error("UI reset failed | status=%d | body=%s", response.status_code, truncate_payload(response.text, 300))
            st.sidebar.error(f"❌ Reset failed: {response.text}")
    except Exception as e:
        logger.exception("UI reset error")
        st.sidebar.error(f"❌ Error: {e}")
    finally:
        reset_request_context(tokens)

st.sidebar.divider()
st.sidebar.info("💡 Use the **📚 Interface Library** tab to see all available interfaces and usage logs.")


# ── Main tabs ─────────────────────────────────────────────────────────
tab_chat, tab_library, tab_metrics = st.tabs(["💬 Chat", "📚 Interface Library", "📊 Query Metrics"])


# ════════════════════════════════════════════════════════════════════
# TAB 1 — CHAT
# ════════════════════════════════════════════════════════════════════
with tab_chat:
    st.title("📊 Stock Agent Chat")
    st.caption("Ask questions about Indian stocks in natural language. Follow-up questions are supported.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("chart"):
                chart_path_str = str(msg["chart"])
                try:
                    st.image(chart_path_str)
                except Exception as e:
                    st.caption(f"Chart: {chart_path_str}")
            if msg.get("tool"):
                from_hist = msg.get("args_from_history") or []
                label = f"Tool: `{msg['tool']}` | Args: `{msg['args']}` | Latency: {msg['latency']:.0f}ms"
                if from_hist:
                    label += f" | From history: `{from_hist}`"
                st.caption(label)

    if prompt := st.chat_input("Ask about Indian stocks..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        call_api_and_render(prompt)


# ════════════════════════════════════════════════════════════════════
# TAB 2 — INTERFACE LIBRARY
# ════════════════════════════════════════════════════════════════════
with tab_library:
    st.title("📚 Interface Library")
    st.caption(
        "All interfaces (tools) registered in the system, and a log of which interfaces "
        "were used for each query — including parameters inherited from previous queries."
    )

    # ── Section 1: Registered interfaces ────────────────────────────
    st.subheader("🔧 Registered Interfaces")
    st.markdown("Dynamically generated Python functions. New interfaces are created on-demand when a query cannot be handled by existing ones.")

    try:
        interfaces_resp = requests.get(f"{API_BASE}/api/tools", timeout=5)
        if interfaces_resp.ok:
            interfaces = interfaces_resp.json()
            if not interfaces:
                st.info("No interfaces generated yet. Ask a question in the Chat tab to create one!")
            else:
                for tool in interfaces:
                    name = tool["name"]
                    icon = "✨" if tool.get("is_new") else "🔧"
                    with st.expander(f"{icon}  `{name}`", expanded=False):
                        st.markdown(f"**Description:** {tool['description']}")
                        if tool.get("code"):
                            st.code(tool["code"], language="python")
                        if tool.get("test_query"):
                            st.caption(f"Created for: {tool['test_query']}")
                        if tool.get("created_at"):
                            st.caption(f"Created: {tool['created_at']}")
                        if tool.get("call_count"):
                            st.metric("Call count", tool["call_count"], label_visibility="collapsed")
        else:
            st.warning("Could not fetch interfaces from API.")
    except requests.RequestException:
        st.warning("API server not reachable.")

    st.divider()

    # ── Section 2: Interface usage log ──────────────────────────────
    st.subheader("🗂️ Interface Usage Log")
    st.markdown(
        "Every query processed this session — which tool was called, "
        "which parameters came from the **current query** vs **inherited from history**."
    )

    log = st.session_state.get("interface_log", [])

    if not log:
        st.info("No queries yet. Go to the Chat tab and ask something to see the log here.")
    else:
        # Summary stats
        total = len(log)
        with_history = sum(1 for e in log if e.get("args_from_history"))
        crr_values = []
        for e in log:
            args = e.get("args") or {}
            from_hist = e.get("args_from_history") or []
            if args:
                crr = len(from_hist) / len(args) * 100
                crr_values.append(crr)

        avg_crr = sum(crr_values) / len(crr_values) if crr_values else 0

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Queries", total)
        m2.metric("Queries Using History", f"{with_history} / {total}")
        m3.metric("Avg Code Reuse Rate", f"{avg_crr:.1f}%")

        st.divider()

        # Per-query breakdown
        for i, entry in enumerate(reversed(log), 1):
            tool = entry.get("tool") or "None"
            args = entry.get("args") or {}
            from_hist = entry.get("args_from_history") or []
            current_args = [k for k in args if k not in from_hist]
            crr = len(from_hist) / len(args) * 100 if args else 0
            icon = TOOL_ICONS.get(tool, "🔧")

            with st.expander(
                f"**Q{total - i + 1}** — `{tool}` {icon} | CRR: {crr:.0f}% | {entry['latency_ms']:.0f}ms",
                expanded=(i == 1),
            ):
                st.markdown(f"**Query:** {entry['query']}")
                st.markdown(f"**Interface used:** `{tool}`")

                col_curr, col_hist = st.columns(2)
                with col_curr:
                    st.markdown("**Parameters from current query:**")
                    if current_args:
                        for k in current_args:
                            st.success(f"`{k}` = `{args[k]}`")
                    else:
                        st.info("All parameters from history")

                with col_hist:
                    st.markdown("**Parameters from previous query:**")
                    if from_hist:
                        for k in from_hist:
                            st.warning(f"`{k}` = `{args.get(k)}`")
                    else:
                        st.info("No parameters from history (CRR = 0%)")


# ════════════════════════════════════════════════════════════════════
# TAB 3 — QUERY METRICS
# ════════════════════════════════════════════════════════════════════
with tab_metrics:
    st.title("📊 Query Metrics")

    # Get the metrics log
    log = st.session_state.get("interface_log", [])

    if not log:
        st.info("No queries yet. Go to the Chat tab and ask something to see metrics here.")
    else:
        # Display metrics for each query
        for i, entry in enumerate(reversed(log), 1):
            query_num = len(log) - i + 1
            query = entry.get("query", "N/A")
            args = entry.get("args") or {}
            from_hist = entry.get("args_from_history") or []
            is_new = entry.get("is_new", False)
            latency = entry.get("latency_ms", 0)
            token_usage = entry.get("token_usage", 0)
            mode = entry.get("mode", "interface")
            
            # Calculate metrics for this query
            # For baseline mode, interface reuse is always 0%
            if mode == "baseline":
                interface_reuse = "0%"
                crr = 0  # Baseline doesn't inherit parameters
            else:
                interface_reuse = "0%" if is_new else "100%"
                crr = (len(from_hist) / len(args) * 100) if args else 0
            
            mode_badge = "🔧 Interface Agent" if mode == "interface" else "📝 General LLM"
            st.subheader(f"Query {query_num}: {query} [{mode_badge}]")
            
            # Display 4 metrics in columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Interface Reuse Rate", interface_reuse)
            
            with col2:
                st.metric("Code Reuse Rate", f"{crr:.1f}%")
            
            with col3:
                st.metric("Token Usage", f"{token_usage}")
            
            with col4:
                st.metric("Latency", f"{latency:.0f}ms")
            
            st.divider()

