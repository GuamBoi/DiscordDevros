import requests
from config import OPENWEBUI_API_URL, OPENWEBUI_API_KEY

async def query_llm(prompt):
    """Send a request to the LLM API and return the generated response."""
    if not OPENWEBUI_API_URL or not OPENWEBUI_API_KEY:
        return "Error: OpenWebUI API settings are missing."

    headers = {
        'Authorization': f'Bearer {OPENWEBUI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "inputs": prompt
    }

    try:
        response = requests.post(OPENWEBUI_API_URL, json=data, headers=headers)
        if response.status_code == 200:
            json_data = response.json()
            return json_data.get("generated_text", "No response generated.")
        else:
            return f"API Error: {response.status_code}"
    except Exception as e:
        return f"Request Failed: {e}"
