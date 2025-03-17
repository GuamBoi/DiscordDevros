import aiohttp
from config import OPENWEBUI_API_URL, OPENWEBUI_API_KEY, MODEL_NAME

async def query_llm(ctx, prompt):
    """Send a request to the LLM API and return the generated response with typing indicator."""
    if not OPENWEBUI_API_URL or not OPENWEBUI_API_KEY:
        return "Error: OpenWebUI URL and/or API settings are missing."

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
                        response_text = json_data.get("choices", [{}])[0].get("message", {}).get("content", "No response generated.")

                        # Check for member mentions in the response
                        response_text = await inject_mentions(ctx, response_text)

                        return response_text
                    else:
                        return f"API Error: {response.status}"
        except Exception as e:
            return f"Request Failed: {e}"


async def inject_mentions(ctx, response_text):
    """Check if any server member's name appears in the response and replace it with a mention."""
    for member in ctx.guild.members:
        # Check if the member's display name or username is in the response
        if member.display_name in response_text or member.name in response_text:
            # Replace the name with a proper mention
            response_text = response_text.replace(member.display_name, f"<@{member.id}>")
            response_text = response_text.replace(member.name, f"<@{member.id}>")

    return response_text
