"""
domain/exceptions/common_exceptions.py

Why this file exists:
    Some errors aren't specific to one bounded context (auth, chat,
    memory) — "you don't own this resource" applies identically across
    conversations, memories, and documents. Rather than duplicating an
    *AccessDeniedError per entity, this shared error keeps the intent
    explicit while avoiding proliferation of near-identical classes.
"""


class AccessDeniedError(Exception):
    def __init__(self, resource: str = "resource"):
        super().__init__(f"You do not have access to this {resource}")
