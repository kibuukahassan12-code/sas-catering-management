from collections import defaultdict, deque
from typing import Deque, Dict, List, TypedDict


class ConversationTurn(TypedDict):
    role: str  # "user" or "ai"
    text: str


class ConversationMemory:
    """
    In-memory, per-user conversation memory.
    Phase 1: ephemeral (no DB writes).
    """

    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self.store: Dict[int, Deque[ConversationTurn]] = defaultdict(
            lambda: deque(maxlen=max_turns)
        )

    def add(self, user_id, role: str, text: str) -> None:
        """
        Add a plain-text turn to memory.

        This is intentionally minimal:
        - No objects or ORM models
        - No SQL result sets
        - No tokens or secrets
        """
        if text is None:
            return
        # Store only simple text payloads; callers are responsible for
        # avoiding sensitive data like passwords or tokens.
        self.store[user_id].append(
            {
                "role": role,
                "text": str(text),
            }
        )

    def get(self, user_id) -> List[ConversationTurn]:
        return list(self.store[user_id])

    def clear(self, user_id) -> None:
        self.store[user_id].clear()


# Single global, in-memory instance for all SAS AI chat usage.
conversation_memory = ConversationMemory()


