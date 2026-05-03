"""FastAPI Web Service for Multi-Mode Learning Assistant"""

from dotenv import load_dotenv
load_dotenv()

import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from Assistant.agent import AgentLoopRunner
from Assistant.openai_provider import OpenAIProvider
from Assistant.context import Context
from Assistant.progress import KnowledgeProgress
from Assistant import config


# ========== Pydantic Models ==========

class InitRequest(BaseModel):
    model: Optional[str] = None


class ChatRequest(BaseModel):
    session_id: str
    message: str


class SwitchStateRequest(BaseModel):
    session_id: str
    target_state: str
    reason: Optional[str] = None


class TodoActionRequest(BaseModel):
    session_id: str
    action: str
    concept: Optional[str] = None
    priority: Optional[int] = None
    item_id: Optional[int] = None


class ProgressRequest(BaseModel):
    session_id: str


# ========== Session Management ==========

class Session:
    def __init__(self, session_id: str, provider: OpenAIProvider, model: str):
        self.session_id = session_id
        self.agent = AgentLoopRunner(provider, model)
        self.agent.register_state_machine("state_machine.yaml")


_sessions: dict[str, Session] = {}

def get_or_create_session(session_id: str) -> Session:
    if session_id not in _sessions:
        provider = OpenAIProvider(
            api_key=config.LLM_API_KEY,
            base_url=config.LLM_BASE_URL,
            timeout=config.LLM_TIMEOUT,
        )
        model = config.LLM_MODEL
        _sessions[session_id] = Session(session_id, provider, model)
    return _sessions[session_id]


# ========== Lifespan ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    _sessions.clear()


# ========== FastAPI App ==========

app = FastAPI(
    title="Multi-Mode Learning Assistant API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== Static Files ==========

import os
web_dir = os.path.join(os.path.dirname(__file__), "web")
if os.path.exists(web_dir):
    app.mount("/static", StaticFiles(directory=web_dir), name="static")


# ========== API Endpoints ==========

@app.get("/")
async def root():
    return FileResponse(os.path.join(os.path.dirname(__file__), "web", "index.html"))


@app.post("/api/init")
async def init_session(req: InitRequest):
    session_id = str(uuid.uuid4())
    session = get_or_create_session(session_id)
    if req.model:
        session.agent.model = req.model
    return {
        "session_id": session_id,
        "current_state": session.agent.current_state,
        "model": session.agent.model
    }


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = _sessions[session_id]
    return {
        "session_id": session_id,
        "current_state": session.agent.current_state,
        "model": session.agent.model,
        "progress": session.agent.progress.progress_summary()
    }


@app.post("/api/chat")
async def chat(req: ChatRequest):
    session = get_or_create_session(req.session_id)
    response = session.agent.send_message(req.message)
    return {
        "response": response,
        "current_state": session.agent.current_state
    }


@app.post("/api/switch_state")
async def switch_state(req: SwitchStateRequest):
    session = get_or_create_session(req.session_id)
    result = session.agent.switch_state(req.target_state, req.reason)
    return {
        "result": result,
        "current_state": session.agent.current_state
    }


@app.post("/api/todo")
async def todo(req: TodoActionRequest):
    session = get_or_create_session(req.session_id)
    tool = session.agent.tools.get("todo_list")
    if not tool:
        raise HTTPException(status_code=400, detail="todo_list tool not available")
    result = tool.execute(
        action=req.action,
        concept=req.concept,
        priority=req.priority,
        item_id=req.item_id
    )
    return {"result": result}


@app.post("/api/progress")
async def progress(req: ProgressRequest):
    session = get_or_create_session(req.session_id)
    return {"progress": session.agent.progress.progress_summary()}


# ========== Main ==========

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)
