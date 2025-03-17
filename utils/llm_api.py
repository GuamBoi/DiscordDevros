import aiohttp
from config import OPENWEBUI_API_URL, OPENWEBUI_API_KEY, MODEL_NAME

async def query_llm(ctx, prompt):
    """Send a request to the LLM API and return the generated response with typing indicator."""
    if not OPENWEBUI_API_URL or not OPENWEBUI_API_KEY:
        return "Error: OpenWebUI API settings are missing."

    # Show typing indicator while waiting for the LLM response
    async with ctx.typing():
        headers = {
            'Authorization': f'Bearer {OPENWEBUI_API_KEY}',
            'Content-Type': 'application/json'
        }

        data = {
            "model": MODEL_NAME,  # Uses the model from the config
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(OPENWEBUI_API_URL, json=data, headers=headers) as response:
                    if response.status == 200:
                        json_data = await response.json()
                        # Assuming OpenWebUI returns "choices" with a "message" object in its response
                        return json_data.get("choices", [{}])[0].get("message", {}).get("content", "No response generated.")
                    else:
                        return f"API Error: {response.status}"
        except Exception as e:
            return f"Request Failed: {e}"
