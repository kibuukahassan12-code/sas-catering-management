from sas_management.ai.engine import SASAIEngine

_engine = SASAIEngine()


def legacy_chat_handler(message, user):
    """
    Adapter for legacy sas_ai routes.
    """
    return _engine.answer(message, user)


