"""
domain/exceptions/chat_exceptions.py

Why this file exists:
    Framework-agnostic errors raised by chat use cases, translated to HTTP
    responses only at the API boundary.
"""


class ChatError(Exception):
    """Base class for all chat/conversation domain errors."""


class ConversationNotFoundError(ChatError):
    def __init__(self, conversation_id):
        super().__init__(f"Conversation not found: {conversation_id}")


class ConversationAccessDeniedError(ChatError):
    def __init__(self):
        super().__init__("You do not have access to this conversation")
