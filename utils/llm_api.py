import aiohttp
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
        "model": "your_model_name",  # Specify the model you want to use
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(OPENWEBUI_API_URL, json=data, headers=headers) as response:
                if response.status == 200:
                    json_data = await response.json()
                    return json_data.get("generated_text", "No response generated.")
                else:
                    return f"API Error: {response.status}"
    except Exception as e:
        return f"Request Failed: {e}"
