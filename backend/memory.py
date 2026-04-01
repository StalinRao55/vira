from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class Memory:
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = Path(storage_path or Path(__file__).with_name(".vira_state.json"))
        self.default_preferences = {
            "theme": "dark",
            "response_style": "balanced",
            "persona": "professional",
            "temperature": 0.3,
            "use_rag": True,
            "use_agents": False,
            "voice_enabled": False,
            "streaming_enabled": True,
            "wide_mode": True,
            "distraction_free": False,
            "show_sources": True,
            "privacy_mode": False,
            "model": "smart",
        }
        self.default_prompts = [
            {"id": "answer", "name": "/answer", "content": "Answer this professionally and directly. Start with the main answer, then add key supporting details.", "scope": "global"},
            {"id": "research", "name": "/research", "content": "Research this topic and provide a clear explanation, the most important facts, and credible sources.", "scope": "global"},
            {"id": "analyze", "name": "/analyze", "content": "Analyze this carefully and give a structured, professional response with conclusions and next steps.", "scope": "global"},
        ]
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.folders: Dict[str, Dict[str, Any]] = {}
        self.prompt_library: List[Dict[str, Any]] = []
        self.schedules: List[Dict[str, Any]] = []
        self.shares: Dict[str, Dict[str, Any]] = {}
        self.audit_logs: List[Dict[str, Any]] = []
        self.analytics: Dict[str, Any] = {
            "total_messages": 0,
            "user_messages": 0,
            "assistant_messages": 0,
            "agent_runs": 0,
            "documents_uploaded": 0,
            "shared_threads": 0,
            "scheduled_tasks": 0,
            "last_activity": None,
        }
        self._load()

    def _timestamp(self) -> str:
        return datetime.utcnow().isoformat()

    def _new_folder(self, folder_id: str, name: str) -> Dict[str, Any]:
        now = self._timestamp()
        return {"id": folder_id, "name": name, "created_at": now, "updated_at": now}

    def _new_session(self, session_id: str, title: Optional[str] = None, folder_id: Optional[str] = None) -> Dict[str, Any]:
        now = self._timestamp()
        return {
            "id": session_id,
            "title": title or "New chat",
            "created_at": now,
            "updated_at": now,
            "history": [],
            "summary": "",
            "preferences": deepcopy(self.default_preferences),
            "folder_id": folder_id or "general",
            "branch_of": None,
            "version": 1,
            "token_estimate": 0,
        }

    def _serialize(self) -> Dict[str, Any]:
        return {
            "sessions": self.sessions,
            "folders": self.folders,
            "prompt_library": self.prompt_library,
            "schedules": self.schedules,
            "shares": self.shares,
            "audit_logs": self.audit_logs[-1000:],
            "analytics": self.analytics,
        }

    def _load(self):
        if self.storage_path.exists():
            try:
                payload = json.loads(self.storage_path.read_text(encoding="utf-8"))
                self.sessions = payload.get("sessions", {})
                self.folders = payload.get("folders", {})
                self.prompt_library = payload.get("prompt_library", deepcopy(self.default_prompts))
                self.schedules = payload.get("schedules", [])
                self.shares = payload.get("shares", {})
                self.audit_logs = payload.get("audit_logs", [])
                self.analytics = {**self.analytics, **payload.get("analytics", {})}
            except Exception:
                self.sessions = {}
                self.folders = {}
                self.prompt_library = []
                self.schedules = []
                self.shares = {}
                self.audit_logs = []
        if not self.prompt_library:
            self.prompt_library = deepcopy(self.default_prompts)
        if "general" not in self.folders:
            self.folders["general"] = self._new_folder("general", "General")
        self._persist()

    def _persist(self):
        self.storage_path.write_text(json.dumps(self._serialize(), indent=2), encoding="utf-8")

    def _estimate_tokens(self, session_id: str) -> int:
        session = self.ensure_session(session_id)
        return sum(max(1, len(item["content"]) // 4) for item in session["history"])

    def _log(self, action: str, entity_type: str, entity_id: str, details: Optional[Dict[str, Any]] = None):
        self.audit_logs.append(
            {
                "timestamp": self._timestamp(),
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "details": details or {},
            }
        )
        self.audit_logs = self.audit_logs[-1000:]
        self._persist()

    def ensure_session(self, session_id: str, title: Optional[str] = None, folder_id: Optional[str] = None) -> Dict[str, Any]:
        if session_id not in self.sessions:
            self.sessions[session_id] = self._new_session(session_id, title=title, folder_id=folder_id)
            self._persist()
        return self.sessions[session_id]

    def create_session(self, session_id: str, title: Optional[str] = None, folder_id: Optional[str] = None) -> Dict[str, Any]:
        session = self._new_session(session_id, title=title, folder_id=folder_id)
        self.sessions[session_id] = session
        self._persist()
        self._log("create", "session", session_id, {"title": session["title"], "folder_id": session["folder_id"]})
        return deepcopy(session)

    def branch_session(self, source_session_id: str, new_session_id: str, message_index: int) -> Dict[str, Any]:
        source = self.ensure_session(source_session_id)
        session = self._new_session(
            new_session_id,
            title=f"{source['title']} v{int(source.get('version', 1)) + 1}",
            folder_id=source.get("folder_id"),
        )
        session["history"] = deepcopy(source["history"][: message_index + 1])
        session["branch_of"] = source_session_id
        session["version"] = int(source.get("version", 1)) + 1
        session["summary"] = source.get("summary", "")
        session["preferences"] = deepcopy(source["preferences"])
        session["token_estimate"] = sum(max(1, len(item["content"]) // 4) for item in session["history"])
        self.sessions[new_session_id] = session
        self._persist()
        self._log("branch", "session", new_session_id, {"source_session_id": source_session_id, "message_index": message_index})
        return deepcopy(session)

    def list_sessions(self) -> List[Dict[str, Any]]:
        sessions = []
        for session in self.sessions.values():
            sessions.append(
                {
                    "id": session["id"],
                    "title": session["title"],
                    "created_at": session["created_at"],
                    "updated_at": session["updated_at"],
                    "message_count": len(session["history"]),
                    "summary": session["summary"],
                    "folder_id": session.get("folder_id"),
                    "branch_of": session.get("branch_of"),
                    "version": session.get("version", 1),
                    "token_estimate": session.get("token_estimate", 0),
                }
            )
        return sorted(sessions, key=lambda item: item["updated_at"], reverse=True)

    def rename_session(self, session_id: str, title: str) -> Dict[str, Any]:
        session = self.ensure_session(session_id)
        session["title"] = title or session["title"]
        session["updated_at"] = self._timestamp()
        self._persist()
        self._log("rename", "session", session_id, {"title": session["title"]})
        return deepcopy(session)

    def move_session(self, session_id: str, folder_id: str) -> Dict[str, Any]:
        session = self.ensure_session(session_id)
        if folder_id not in self.folders:
            self.folders[folder_id] = self._new_folder(folder_id, folder_id.title())
        session["folder_id"] = folder_id
        session["updated_at"] = self._timestamp()
        self._persist()
        self._log("move", "session", session_id, {"folder_id": folder_id})
        return deepcopy(session)

    def add(self, session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        session = self.ensure_session(session_id)
        message = {"role": role, "content": content, "timestamp": self._timestamp(), "metadata": metadata or {}}
        session["history"].append(message)
        session["updated_at"] = message["timestamp"]
        session["token_estimate"] = self._estimate_tokens(session_id)
        self.analytics["total_messages"] += 1
        if role == "user":
            self.analytics["user_messages"] += 1
        elif role == "assistant":
            self.analytics["assistant_messages"] += 1
        self.analytics["last_activity"] = message["timestamp"]
        if role == "user" and len(session["history"]) == 1:
            session["title"] = content[:50] or session["title"]
        self._refresh_summary(session_id)
        self._persist()

    def update_message(self, session_id: str, message_index: int, content: str) -> Dict[str, Any]:
        session = self.ensure_session(session_id)
        if message_index < 0 or message_index >= len(session["history"]):
            raise IndexError("Message index out of range")
        session["history"][message_index]["content"] = content
        session["history"][message_index]["metadata"]["edited"] = True
        session["history"][message_index]["metadata"]["edited_at"] = self._timestamp()
        session["updated_at"] = self._timestamp()
        session["token_estimate"] = self._estimate_tokens(session_id)
        self._refresh_summary(session_id)
        self._persist()
        self._log("edit", "message", f"{session_id}:{message_index}", {"session_id": session_id})
        return deepcopy(session)

    def _refresh_summary(self, session_id: str):
        session = self.ensure_session(session_id)
        recent_user_prompts = [item["content"][:160] for item in session["history"] if item["role"] == "user"][-3:]
        session["summary"] = " | ".join(recent_user_prompts) if recent_user_prompts else ""

    def get(self, session_id: str) -> List[Dict[str, Any]]:
        return deepcopy(self.ensure_session(session_id)["history"])

    def get_session(self, session_id: str) -> Dict[str, Any]:
        return deepcopy(self.ensure_session(session_id))

    def update_preferences(self, session_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        session = self.ensure_session(session_id)
        session["preferences"].update({k: v for k, v in preferences.items() if v is not None})
        session["updated_at"] = self._timestamp()
        self._persist()
        self._log("update", "preferences", session_id, preferences)
        return deepcopy(session["preferences"])

    def get_preferences(self, session_id: str) -> Dict[str, Any]:
        return deepcopy(self.ensure_session(session_id)["preferences"])

    def create_folder(self, folder_id: str, name: str) -> Dict[str, Any]:
        folder = self._new_folder(folder_id, name)
        self.folders[folder_id] = folder
        self._persist()
        self._log("create", "folder", folder_id, {"name": name})
        return deepcopy(folder)

    def list_folders(self) -> List[Dict[str, Any]]:
        folders = []
        for folder in self.folders.values():
            folders.append({**deepcopy(folder), "session_count": len([item for item in self.sessions.values() if item.get("folder_id") == folder["id"]])})
        return sorted(folders, key=lambda item: item["updated_at"], reverse=True)

    def add_prompt(self, prompt_id: str, name: str, content: str, scope: str = "workspace") -> Dict[str, Any]:
        prompt = {"id": prompt_id, "name": name, "content": content, "scope": scope}
        self.prompt_library = [item for item in self.prompt_library if item["id"] != prompt_id] + [prompt]
        self._persist()
        self._log("create", "prompt", prompt_id, {"name": name})
        return deepcopy(prompt)

    def list_prompts(self) -> List[Dict[str, Any]]:
        return deepcopy(self.prompt_library)

    def create_schedule(self, schedule_id: str, title: str, prompt: str, cron_label: str) -> Dict[str, Any]:
        schedule = {
            "id": schedule_id,
            "title": title,
            "prompt": prompt,
            "cron_label": cron_label,
            "created_at": self._timestamp(),
            "last_run_at": None,
            "status": "scheduled",
        }
        self.schedules = [item for item in self.schedules if item["id"] != schedule_id] + [schedule]
        self.analytics["scheduled_tasks"] = len(self.schedules)
        self._persist()
        self._log("create", "schedule", schedule_id, {"title": title, "cron_label": cron_label})
        return deepcopy(schedule)

    def list_schedules(self) -> List[Dict[str, Any]]:
        return deepcopy(self.schedules)

    def create_share(self, share_id: str, session_id: str, mode: str = "view") -> Dict[str, Any]:
        session = self.ensure_session(session_id)
        share = {"id": share_id, "session_id": session_id, "mode": mode, "created_at": self._timestamp(), "title": session["title"]}
        self.shares[share_id] = share
        self.analytics["shared_threads"] = len(self.shares)
        self._persist()
        self._log("share", "session", session_id, {"share_id": share_id, "mode": mode})
        return deepcopy(share)

    def get_share(self, share_id: str) -> Dict[str, Any]:
        share = self.shares[share_id]
        return {"share": deepcopy(share), "session": self.get_session(share["session_id"])}

    def increment_documents(self):
        self.analytics["documents_uploaded"] += 1
        self.analytics["last_activity"] = self._timestamp()
        self._persist()

    def increment_agent_runs(self):
        self.analytics["agent_runs"] += 1
        self.analytics["last_activity"] = self._timestamp()
        self._persist()

    def list_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        return deepcopy(self.audit_logs[-limit:])

    def clear(self, session_id: Optional[str] = None):
        if session_id:
            existing = self.ensure_session(session_id)
            self.sessions[session_id] = self._new_session(session_id, title=existing["title"], folder_id=existing.get("folder_id"))
            self._persist()
            self._log("clear", "session", session_id)
            return
        self.sessions = {}
        self.folders = {"general": self._new_folder("general", "General")}
        self.prompt_library = deepcopy(self.default_prompts)
        self.schedules = []
        self.shares = {}
        self.audit_logs = []
        self.analytics.update(
            {
                "total_messages": 0,
                "user_messages": 0,
                "assistant_messages": 0,
                "agent_runs": 0,
                "documents_uploaded": 0,
                "shared_threads": 0,
                "scheduled_tasks": 0,
                "last_activity": None,
            }
        )
        self._persist()

    def get_analytics(self) -> Dict[str, Any]:
        session_count = len(self.sessions)
        avg_messages = round(sum(len(session["history"]) for session in self.sessions.values()) / session_count, 2) if session_count else 0
        return {
            **deepcopy(self.analytics),
            "total_sessions": session_count,
            "average_messages_per_session": avg_messages,
            "folder_count": len(self.folders),
            "prompt_count": len(self.prompt_library),
        }
