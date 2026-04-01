from datetime import datetime
from typing import Optional
from uuid import uuid4
import io
import csv

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agents import agent_system
from llm import generate_response
from memory import Memory
from rag import rag_system
from voice import voice_system
import os
import logging
import subprocess

logger = logging.getLogger(__name__)

app = FastAPI(
    title="VIRA AI - Advanced Chatbot System",
    description="A comprehensive AI chatbot with RAG, agents, and voice capabilities",
    version="2.0.0"
)

memory = Memory()


class ChatRequest(BaseModel):
    session_id: str = Field(default="default")
    message: str = Field(min_length=1, max_length=8000)
    use_rag: bool = True
    use_agents: bool = False
    use_web: bool = False
    speak: bool = False
    streaming: bool = True
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    persona: Optional[str] = None
    response_style: Optional[str] = None
    model: Optional[str] = None
    privacy_mode: bool = False


class AgentRequest(BaseModel):
    session_id: str = Field(default="default")
    task: str = Field(min_length=1, max_length=4000)


class VoiceRequest(BaseModel):
    text: Optional[str] = ""
    action: str = "speak"


class SessionCreateRequest(BaseModel):
    title: Optional[str] = "New chat"
    folder_id: Optional[str] = "general"


class SessionRenameRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)


class PreferencesRequest(BaseModel):
    theme: Optional[str] = None
    response_style: Optional[str] = None
    persona: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    use_rag: Optional[bool] = None
    use_agents: Optional[bool] = None
    voice_enabled: Optional[bool] = None
    streaming_enabled: Optional[bool] = None
    wide_mode: Optional[bool] = None
    distraction_free: Optional[bool] = None
    show_sources: Optional[bool] = None
    privacy_mode: Optional[bool] = None
    model: Optional[str] = None


class FolderRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class PromptRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=4000)
    scope: str = "workspace"


class ScheduleRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    prompt: str = Field(min_length=1, max_length=4000)
    cron_label: str = Field(min_length=1, max_length=120)


class ShareRequest(BaseModel):
    session_id: str
    mode: str = "view"


class BranchRequest(BaseModel):
    session_id: str
    message_index: int = Field(ge=0)


class MessageEditRequest(BaseModel):
    session_id: str
    message_index: int = Field(ge=0)
    content: str = Field(min_length=1, max_length=8000)


class PythonRunRequest(BaseModel):
    code: str = Field(min_length=1, max_length=12000)


def model_to_dict(model: BaseModel) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=True)
    return model.dict(exclude_none=True)


def build_export_text(session: dict) -> str:
    lines = [f"# {session['title']}", ""]
    if session.get("summary"):
        lines.extend(["Summary:", session["summary"], ""])
    for item in session.get("history", []):
        lines.append(f"[{item['role'].upper()}] {item['timestamp']}")
        lines.append(item["content"])
        if item.get("metadata", {}).get("sources"):
            lines.append("Sources:")
            for source in item["metadata"]["sources"]:
                lines.append(f"- {source.get('source', source.get('title', 'source'))}")
        lines.append("")
    return "\n".join(lines).strip()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "message": "VIRA AI Backend Running",
        "features": [
            "Conversational AI",
            "RAG System",
            "Agent System", 
            "Voice Processing",
            "Document Upload",
            "Memory Management",
            "Session History",
            "Analytics",
            "Personalization",
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.post("/chat")
async def chat(data: ChatRequest):
    """Enhanced chat endpoint with RAG and agent integration"""
    try:
        session = memory.ensure_session(data.session_id)
        preferences_update = {
            "use_rag": data.use_rag,
            "use_agents": data.use_agents,
            "voice_enabled": data.speak,
            "streaming_enabled": data.streaming,
            "temperature": data.temperature,
            "privacy_mode": data.privacy_mode,
        }
        if data.persona:
            preferences_update["persona"] = data.persona
        if data.response_style:
            preferences_update["response_style"] = data.response_style
        if data.model:
            preferences_update["model"] = data.model
        preferences = memory.update_preferences(data.session_id, preferences_update)
        
        user_input = data.message.strip()
        sources = []
        if data.use_rag:
            sources.extend(rag_system.get_sources(user_input))
        if data.use_web:
            sources.extend(agent_system.web_search_results(user_input, limit=4))
        
        if not data.privacy_mode:
            memory.add(data.session_id, "user", user_input, metadata={"privacy_mode": False})
        
        # Generate response with enhanced features
        response = generate_response(
            memory.get(data.session_id) if not data.privacy_mode else session.get("history", []),
            user_input,
            preferences=preferences,
            session_summary=session.get("summary", ""),
            temperature=data.temperature,
        )
        
        # Execute agent tasks if requested
        agent_response = ""
        if data.use_agents:
            agent_response = agent_system.execute_agent_task(user_input)
            memory.increment_agent_runs()
        
        # Convert response to speech if requested
        if data.speak:
            voice_system.text_to_speech(response)
        
        if not data.privacy_mode:
            memory.add(
                data.session_id,
                "assistant",
                response,
                metadata={
                    "rag_enabled": data.use_rag,
                    "agents_enabled": data.use_agents,
                    "streaming_enabled": data.streaming,
                    "sources": sources,
                    "model": preferences.get("model", "smart"),
                },
            )
            refreshed_session = memory.get_session(data.session_id)
        else:
            refreshed_session = memory.get_session(data.session_id)
        
        return {
            "response": response,
            "agent_response": agent_response,
            "sources": sources,
            "memory_length": len(refreshed_session["history"]),
            "session": {
                "id": refreshed_session["id"],
                "title": refreshed_session["title"],
                "summary": refreshed_session["summary"],
                "updated_at": refreshed_session["updated_at"],
                "folder_id": refreshed_session.get("folder_id"),
                "version": refreshed_session.get("version", 1),
                "token_estimate": refreshed_session.get("token_estimate", 0),
            },
            "preferences": refreshed_session["preferences"],
            "token_usage": {
                "used": refreshed_session.get("token_estimate", 0),
                "window": 32000 if preferences.get("model", "smart") == "fast" else 128000,
            },
            "privacy_mode": data.privacy_mode,
        }
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return {"error": str(e), "response": "I apologize, but I'm having trouble processing your request."}

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = Form(default="default"),
):
    """Upload documents for RAG system"""
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save uploaded file
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Add document to RAG system
        rag_system.add_document(file_path, {
            "filename": file.filename,
            "size": len(content),
            "uploaded_at": datetime.utcnow().isoformat(),
            "session_id": session_id,
        })
        memory.increment_documents()
        
        return {
            "message": f"Document '{file.filename}' uploaded and processed successfully",
            "total_documents": len(rag_system.documents),
            "document": {
                "filename": file.filename,
                "size": len(content),
                "session_id": session_id,
            },
        }
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        return {"error": str(e)}

@app.post("/agent")
async def execute_agent(data: AgentRequest):
    """Execute agent tasks"""
    try:
        memory.increment_agent_runs()
        result = agent_system.execute_agent_task(data.task)
        return {"result": result, "session_id": data.session_id}
        
    except Exception as e:
        logger.error(f"Error in agent endpoint: {e}")
        return {"error": str(e)}

@app.post("/voice")
async def voice_processing(data: VoiceRequest):
    """Voice processing endpoint"""
    try:
        text = data.text or ""
        action = data.action
        
        if action == "speak":
            if not text:
                raise HTTPException(status_code=400, detail="Text is required for speech")
            result = voice_system.text_to_speech(text, speak=True)
            return {"message": result}
        
        elif action == "recognize":
            # Placeholder for speech recognition
            result = voice_system.speech_to_text()
            return {"transcription": result}
        
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Use 'speak' or 'recognize'")
            
    except Exception as e:
        logger.error(f"Error in voice endpoint: {e}")
        return {"error": str(e)}

@app.get("/documents")
async def list_documents():
    """List all documents in RAG system"""
    try:
        documents = []
        for doc in rag_system.documents:
            documents.append({
                "filename": os.path.basename(doc['path']),
                "metadata": doc['metadata'],
                "preview": doc['text'][:200]
            })
        return {"documents": documents, "total": len(documents)}
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return {"error": str(e)}


@app.get("/documents/{filename}/summary")
def summarize_document(filename: str):
    return rag_system.summarize_document(filename)

@app.get("/sessions")
def list_sessions():
    return {"sessions": memory.list_sessions()}


@app.post("/sessions")
def create_session(data: SessionCreateRequest):
    session_id = str(uuid4())
    session = memory.create_session(session_id, title=data.title, folder_id=data.folder_id)
    return {"session": session}


@app.patch("/sessions/{session_id}")
def rename_session(session_id: str, data: SessionRenameRequest):
    session = memory.rename_session(session_id, data.title)
    return {"session": session}


@app.post("/sessions/branch")
def branch_session(data: BranchRequest):
    session_id = str(uuid4())
    session = memory.branch_session(data.session_id, session_id, data.message_index)
    return {"session": session}


@app.patch("/messages/edit")
def edit_message(data: MessageEditRequest):
    session = memory.update_message(data.session_id, data.message_index, data.content)
    return {"session": session}


@app.get("/folders")
def list_folders():
    return {"folders": memory.list_folders()}


@app.post("/folders")
def create_folder(data: FolderRequest):
    folder_id = data.name.lower().replace(" ", "-")
    folder = memory.create_folder(folder_id, data.name)
    return {"folder": folder}


@app.patch("/sessions/{session_id}/folder/{folder_id}")
def move_session(session_id: str, folder_id: str):
    session = memory.move_session(session_id, folder_id)
    return {"session": session}


@app.get("/prompts")
def list_prompts():
    return {"prompts": memory.list_prompts()}


@app.post("/prompts")
def create_prompt(data: PromptRequest):
    prompt_id = data.name.strip("/").lower().replace(" ", "-")
    prompt = memory.add_prompt(prompt_id, data.name, data.content, data.scope)
    return {"prompt": prompt}


@app.get("/schedules")
def list_schedules():
    return {"schedules": memory.list_schedules()}


@app.post("/schedules")
def create_schedule(data: ScheduleRequest):
    schedule_id = str(uuid4())
    schedule = memory.create_schedule(schedule_id, data.title, data.prompt, data.cron_label)
    return {"schedule": schedule}


@app.post("/shares")
def create_share(data: ShareRequest):
    share_id = str(uuid4())[:8]
    share = memory.create_share(share_id, data.session_id, data.mode)
    return {"share": share, "url": f"/shared/{share_id}"}


@app.get("/shared/{share_id}")
def get_shared_thread(share_id: str):
    return memory.get_share(share_id)


@app.get("/history/{session_id}")
def get_history(session_id: str):
    session = memory.get_session(session_id)
    return {
        "session_id": session_id,
        "title": session["title"],
        "summary": session["summary"],
        "history": session["history"],
        "preferences": session["preferences"],
        "folder_id": session.get("folder_id"),
        "branch_of": session.get("branch_of"),
        "version": session.get("version", 1),
        "token_estimate": session.get("token_estimate", 0),
    }


@app.get("/preferences/{session_id}")
def get_preferences(session_id: str):
    return {"session_id": session_id, "preferences": memory.get_preferences(session_id)}


@app.patch("/preferences/{session_id}")
def update_preferences(session_id: str, data: PreferencesRequest):
    preferences = memory.update_preferences(session_id, model_to_dict(data))
    return {"session_id": session_id, "preferences": preferences}


@app.get("/analytics")
def analytics():
    recent_documents = [
        {
            "filename": os.path.basename(doc["path"]),
            "metadata": doc["metadata"],
        }
        for doc in rag_system.documents[-5:]
    ]
    return {
        "analytics": memory.get_analytics(),
        "recent_documents": recent_documents,
        "embedding_backend": rag_system.embedding_backend,
    }


@app.get("/audit-logs")
def audit_logs(limit: int = 100):
    return {"logs": memory.list_audit_logs(limit=limit)}


@app.get("/export/{session_id}.txt", response_class=PlainTextResponse)
def export_text(session_id: str):
    session = memory.get_session(session_id)
    return build_export_text(session)


@app.get("/export/{session_id}.md", response_class=PlainTextResponse)
def export_markdown(session_id: str):
    session = memory.get_session(session_id)
    return build_export_text(session)


@app.post("/tools/python")
def run_python_tool(data: PythonRunRequest):
    try:
        result = subprocess.run(
            ["python", "-I", "-c", data.code],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Python tool timed out after 10 seconds.", "returncode": 124}


@app.post("/reset")
def reset(session_id: Optional[str] = None):
    """Reset memory and clear documents"""
    try:
        memory.clear(session_id)
        if not session_id:
            rag_system.documents = []
            rag_system.embeddings = []
            return {"message": "Memory and documents cleared successfully"}
        return {"message": f"Session '{session_id}' cleared successfully"}
        
    except Exception as e:
        logger.error(f"Error resetting system: {e}")
        return {"error": str(e)}

@app.get("/status")
def system_status():
    """Get system status and statistics"""
    try:
        analytics = memory.get_analytics()
        return {
            "status": "operational",
            "memory_entries": analytics["total_messages"],
            "rag_documents": len(rag_system.documents),
            "sessions": analytics["total_sessions"],
            "folders": analytics["folder_count"],
            "analytics": analytics,
            "resources": {
                "embedding_backend": rag_system.embedding_backend,
                "rag_ready": len(rag_system.documents) > 0,
                "agent_tools": len(agent_system.tools),
                "voice_ready": voice_system.available,
                "prompt_library": len(memory.list_prompts()),
                "schedules": len(memory.list_schedules()),
            },
            "features": {
                "rag": True,
                "agents": True,
                "voice": True,
                "document_upload": True,
                "multi_session": True,
                "analytics": True,
                "personalization": True,
                "streaming_ui": True,
                "sharing": True,
                "workspace_folders": True,
                "prompt_library": True,
                "export": True,
                "schedules": True,
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {"error": str(e)}
