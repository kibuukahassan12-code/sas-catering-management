# SAS AI Chat Module

ChatGPT-like conversational AI assistant for SAS Best Foods Catering Management System.

## Setup Instructions

### 1. Update `config.py`

Add to `BaseConfig` class:

```python
# SAS AI Configuration
SAS_AI_ENABLED = os.environ.get("SAS_AI_ENABLED", "true").lower() == "true"
```

### 2. Register Blueprint in `app.py`

Add this code to register the blueprint safely:

```python
# SAS AI Blueprint Registration
try:
    from sas_management.sas_ai import register_sas_ai_blueprint
    register_sas_ai_blueprint(app)
except Exception as e:
    app.logger.warning(f"Could not register SAS AI blueprint: {e}")
```

Or manually:

```python
# SAS AI Blueprint
try:
    from sas_management.sas_ai import sas_ai_bp
    app.config.setdefault("SAS_AI_ENABLED", True)
    app.register_blueprint(sas_ai_bp)
    app.logger.info("SAS AI blueprint registered")
except ImportError as e:
    app.logger.warning(f"SAS AI module not available: {e}")
```

### 3. Access the Chat

- URL: `/sas-ai/chat`
- Requires: User must be logged in
- Config toggle: `app.config["SAS_AI_ENABLED"]` (default: True)

## Features

- ✅ ChatGPT-like interface
- ✅ Conversation memory per session
- ✅ Dynamic AI responses
- ✅ System data queries (events, revenue, staff)
- ✅ General knowledge questions
- ✅ Typing indicator
- ✅ Auto-scroll
- ✅ Responsive design
- ✅ Safe error handling

## Architecture

- `routes.py` - Flask routes and endpoints
- `ai_engine.py` - AI response generation
- `permissions.py` - Feature toggle checking
- `context.py` - System knowledge context
- `templates/sas_ai/chat.html` - Chat UI
- `static/chat.css` - Styles
- `static/chat.js` - Client-side JavaScript

## API Endpoint

```
POST /sas-ai/chat
Content-Type: application/json

{
  "message": "How many events this month?",
  "session_id": "optional-session-id"
}

Response:
{
  "success": true,
  "reply": "AI response text",
  "session_id": "session-id"
}
```

## Configuration

Set `SAS_AI_ENABLED = False` in config to disable the feature. The endpoint will return a safe "offline" message.

