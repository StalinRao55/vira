import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from config import GEMINI_API_KEY, GEMINI_MODEL, SYSTEM_PROMPT, CODEX_SYSTEM_PROMPT
from rag import rag_system

logger = logging.getLogger(__name__)

GENAI_MODE = None
legacy_genai = None
genai = None

if GEMINI_API_KEY:
    try:
        from google import genai
        GENAI_MODE = "google-genai"
    except Exception:  # pragma: no cover - optional dependency at runtime
        try:
            import google.generativeai as legacy_genai
            GENAI_MODE = "google-generativeai"
        except Exception:  # pragma: no cover - optional dependency at runtime
            legacy_genai = None

if GENAI_MODE == "google-genai" and genai and GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
elif GENAI_MODE == "google-generativeai" and legacy_genai and GEMINI_API_KEY:
    legacy_genai.configure(api_key=GEMINI_API_KEY)
    client = legacy_genai.GenerativeModel(GEMINI_MODEL)
else:
    client = None


def _generate_with_timeout(prompt: str, timeout_seconds: int = 30):
    def task():
        if GENAI_MODE == "google-genai":
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config={"http_options": {"timeout": timeout_seconds}},
            )
            return getattr(response, "text", None)
        if GENAI_MODE == "google-generativeai":
            response = client.generate_content(
                prompt,
                request_options={"timeout": timeout_seconds},
            )
            return getattr(response, "text", None)
        return None

    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(task)
    try:
        return future.result(timeout=timeout_seconds + 1)
    except FuturesTimeoutError:
        logger.warning("LLM request timed out and will fall back")
        future.cancel()
        return None
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

def _fallback_response(history, user_query=None, rag_context="", preferences=None, session_summary=""):
    style = (preferences or {}).get("response_style", "balanced")
    persona = (preferences or {}).get("persona", "professional")
    latest_user_message = user_query or (history[-1]["content"] if history else "your request")
    response_parts = [f"VIRA could not reach the full model right now. Your question was: {latest_user_message}"]

    if rag_context:
        response_parts.append("Relevant context found in your uploaded material:")
        response_parts.append(rag_context[:1200])
    elif session_summary:
        response_parts.append(f"Recent conversation context: {session_summary}")
    else:
        response_parts.append(
            "The model backend is currently unavailable or timed out, so the reply is limited."
        )

    if style == "concise":
        response_parts.append("Response style is set to concise.")
    elif style == "detailed":
        response_parts.append("Response style is set to detailed.")
    elif style == "technical":
        response_parts.append("Response style is set to technical.")

    if persona != "professional":
        response_parts.append(f"Persona preference: {persona}.")

    return "\n\n".join(response_parts)


def generate_response(history, user_query=None, preferences=None, session_summary="", temperature=0.7):
    """
    Enhanced response generation with RAG integration
    """
    try:
        # Get RAG context if available
        rag_context = ""
        if user_query:
            rag_context = rag_system.get_context(user_query, max_tokens=1500)
        
        # Build messages
        persona = (preferences or {}).get("persona", "professional")
        style = (preferences or {}).get("response_style", "balanced")
        model = (preferences or {}).get("model", "smart")
        if model == "codex":
            system_prompt = f"{CODEX_SYSTEM_PROMPT}\n\nResponse style: {style}. Code expert mode active."
        else:
            system_prompt = (
                f"{SYSTEM_PROMPT}\n\n"
                f"User persona preference: {persona}\n"
                f"Response style: {style}\n"
            )
        if session_summary:
            system_prompt += f"Conversation summary:\n{session_summary}\n"

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add RAG context if available
        if rag_context:
            rag_message = {
                "role": "system", 
                "content": f"Relevant context from documents:\n{rag_context}"
            }
            messages.append(rag_message)
        
        # Add conversation history
        messages.extend(history)
        
        # Generate response
        if not GEMINI_API_KEY or not client:
            return _fallback_response(
                history,
                user_query=user_query,
                rag_context=rag_context,
                preferences=preferences,
                session_summary=session_summary,
            )

        prompt_sections = []
        for message in messages:
            role = message.get("role", "user").upper()
            prompt_sections.append(f"{role}:\n{message.get('content', '')}")

        prompt = "\n\n".join(prompt_sections)
        text = _generate_with_timeout(prompt, timeout_seconds=30)

        if text:
            return text
        return _fallback_response(
            history,
            user_query=user_query,
            rag_context=rag_context,
            preferences=preferences,
            session_summary=session_summary,
        )
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return _fallback_response(
            history,
            user_query=user_query,
            rag_context=rag_context if "rag_context" in locals() else "",
            preferences=preferences,
            session_summary=session_summary,
        )

def process_voice_input(audio_data):
    """
    Process voice input (placeholder for future implementation)
    """
    # This would integrate with speech recognition
    return "Voice input processing not yet implemented"

def execute_agent_task(task_description):
    """
    Execute agent tasks (placeholder for future implementation)
    """
    # This would integrate with agent frameworks
    return f"Agent task '{task_description}' not yet implemented"
