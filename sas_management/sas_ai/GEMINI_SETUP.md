# Google Gemini AI Integration Setup

The SAS AI Assistant now supports Google Gemini AI for enhanced natural language responses.

## Setup Instructions

### 1. Install the Package

```bash
pip install google-generativeai
```

Or use the requirements file:
```bash
pip install -r requirements_gemini.txt
```

### 2. Get Your API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Create a new API key
4. Copy the API key

### 3. Configure the API Key

**Option A: Environment Variable (Recommended)**
```bash
export GOOGLE_API_KEY="your-api-key-here"
```

**Option B: .env File**
Add to your `.env` file:
```
GOOGLE_API_KEY=your-api-key-here
```

**Option C: Config File**
Add to `config.py`:
```python
GOOGLE_API_KEY = "your-api-key-here"
```

## How It Works

### With Gemini Enabled
- System queries (events, revenue, staff) are enhanced with natural language responses
- General questions use Gemini AI for intelligent answers
- System data is fetched from your database and presented naturally by Gemini

### Without Gemini (Fallback)
- The system falls back to rule-based responses
- All functionality continues to work normally
- No errors if API key is not set

## Features

1. **System Data Integration**
   - Queries your SAS database for events, revenue, staff, inventory
   - Gemini presents this data in natural, conversational responses

2. **General Knowledge**
   - Answers general questions about catering, business, etc.
   - Provides intelligent responses without database queries

3. **Seamless Fallback**
   - If Gemini is unavailable, uses rule-based responses
   - System continues to function normally

## Example Usage

**System Query (with Gemini):**
- User: "How much profit did we make?"
- System fetches revenue data from database
- Gemini: "Based on your database, this month's revenue from 15 accepted quotes is 45,000,000 UGX. Would you like a detailed breakdown?"

**General Question (with Gemini):**
- User: "Give me a slogan for a catering company"
- Gemini: "Here are some catchy slogans for your catering business: 'Fresh flavors, unforgettable moments' or 'We cater to your every need'..."

## Security Notes

- Never commit your API key to version control
- Store it in environment variables or secure config files
- The API key is only used for generating AI responses
- All system data queries use your local database

## Troubleshooting

**Gemini not working?**
- Check that `google-generativeai` is installed
- Verify API key is set correctly
- Check logs for error messages
- System will automatically fall back to rule-based responses

**API Key Invalid?**
- Verify the key is correct
- Check if the key has expired
- Ensure you have API access enabled in Google AI Studio

