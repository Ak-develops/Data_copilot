"""FastAPI backend server — Application Layer entry point.

Endpoints
─────────
POST /api/chat       → accept a natural-language query, return answer + chart
GET  /api/tools      → list all registered tools
POST /api/benchmark  → run evaluation over a test query suite

Run with:
    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request

from config import settings
from logger import (
    generate_id,
    get_logger,
    reset_request_context,
    set_request_context,
    setup_logging,
    truncate_payload,
)

# ── Logging ────────────────────────────────────────────────────────
setup_logging(settings.log_level)
logger = get_logger(__name__)

from schemas import ChatRequest, ChatResponse, ToolInfo, BenchmarkRequest, BenchmarkResult
from services.agent_service import agent_service


# ── Lifespan ────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting Application Layer | host=%s | port=%d | routing=%s | model=%s | dag=%s (threshold=%d) | log_level=%s",
        settings.api_host,
        settings.api_port,
        settings.routing_mode,
        settings.groq_model,
        settings.enable_dag_execution,
        settings.dag_complexity_threshold,
        settings.log_level,
    )
    
    # Auto-seed interface library if empty
    from model.tools import interface_library
    if len(interface_library.list_all()) == 0:
        logger.info("Interface library is empty - auto-seeding with pre-built interfaces...")
        try:
            from seed_library import seed_interface_library
            seed_interface_library()
        except Exception:
            logger.exception("Failed to auto-seed interface library")
    else:
        logger.info("Interface library loaded with %d interfaces", len(interface_library.list_all()))
    
    yield
    logger.info("Shutting down Application Layer")


# ── App ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Stock Agent — Application Layer",
    description="Full-stack infrastructure for the AI stock-analysis agent",
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Attach request/session context and log request lifecycle and unhandled exceptions."""
    request_id = request.headers.get("X-Request-ID") or generate_id("req-")
    session_id = request.headers.get("X-Session-ID") or "-"
    tokens = set_request_context(request_id=request_id, session_id=session_id)
    start = time.perf_counter()

    logger.info("Incoming HTTP %s %s", request.method, request.url.path)
    try:
        response = await call_next(request)
        latency_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "Completed HTTP %s %s | status=%d | latency=%.1fms",
            request.method,
            request.url.path,
            response.status_code,
            latency_ms,
        )
        return response
    except Exception:
        latency_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "Unhandled exception during HTTP %s %s | latency=%.1fms",
            request.method,
            request.url.path,
            latency_ms,
        )
        raise
    finally:
        reset_request_context(tokens)


# ── Routes ──────────────────────────────────────────────────────────

@app.get("/api/tools", response_model=list[ToolInfo])
async def get_tools():
    """Return the current index of tools available in the system."""
    return agent_service.list_tools()


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Accept a user query, invoke the Model Layer, return textual + chart output."""
    if not req.query.strip():
        logger.warning("Rejected empty /api/chat query")
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    logger.info(
        "Chat request | routing_mode=%s | history_turns=%d | query=%s",
        req.routing_mode or settings.routing_mode,
        len(req.history or []),
        truncate_payload(req.query, 500),
    )
    result = agent_service.process_query(req.query, routing_mode=req.routing_mode,
                                          history=req.history)
    logger.info(
        "Chat response | tool=%s | new_interface=%s | tokens=%s | latency=%.1fms",
        result.get("tool_used"),
        result.get("is_new_interface"),
        result.get("token_usage"),
        result.get("latency_ms", 0.0),
    )
    return ChatResponse(**result)


@app.post("/api/chat/baseline", response_model=ChatResponse)
async def chat_baseline(req: ChatRequest):
    """Accept a user query, use baseline agent (no interface reuse), return output."""
    if not req.query.strip():
        logger.warning("Rejected empty /api/chat/baseline query")
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    logger.info("Baseline chat request | query=%s", truncate_payload(req.query, 500))
    from baseline_agent import baseline_agent
    result = baseline_agent.process_query(req.query)
    logger.info(
        "Baseline chat response | has_error=%s | tokens=%s | latency=%.1fms",
        result.get("has_error"),
        result.get("token_usage", {}).get("total_tokens"),
        result.get("latency_ms", 0.0),
    )
    
    # Convert baseline result to ChatResponse format
    return ChatResponse(
        answer=result["answer"],
        tool_used=None,
        tool_args=None,
        args_from_history=[],
        chart_path=result.get("chart_path"),
        routing_mode=req.routing_mode or settings.routing_mode,
        latency_ms=result["latency_ms"],
        is_new_interface=False,  # Baseline doesn't have interfaces
        token_usage=result["token_usage"]["total_tokens"],
    )


@app.post("/api/reset")
async def reset_system():
    """Reset the system: clear all interfaces and rebuild index."""
    try:
        from model.tools import interface_library
        interface_library.clear()
        agent_service._rebuild_index()
        logger.info("System reset: all interfaces cleared")
        return {"status": "success", "message": "All interfaces deleted and index rebuilt"}
    except Exception as e:
        logger.exception("Reset failed")
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


@app.post("/api/benchmark", response_model=BenchmarkResult)
async def benchmark(req: BenchmarkRequest):
    """Run automated batch evaluation over different library sizes and routing modes."""
    # TODO: wire to benchmark.py runner
    raise HTTPException(status_code=501, detail="Benchmark endpoint not yet implemented")


@app.get("/api/health")
async def health():
    """Simple health-check for container orchestration."""
    return {"status": "ok", "routing_mode": settings.routing_mode}


# ── Entrypoint ──────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,  # Disable reload to avoid git conflicts with modified files
    )
