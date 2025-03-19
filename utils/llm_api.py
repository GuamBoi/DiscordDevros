import aiohttp
import re
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
            # Open session for making the request
            async with aiohttp.ClientSession() as session:
                async with session.post(OPENWEBUI_API_URL, json=data, headers=headers) as response:
                    # Check response status
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
        # Make display name and username lowercase for case-insensitive matching
        member_display_name_lower = member.display_name.lower()
        member_name_lower = member.name.lower()
        response_text_lower = response_text.lower()

        # Only proceed if the name exists in the response (case insensitive)
        if member_display_name_lower in response_text_lower or member_name_lower in response_text_lower:
            # Create regex patterns to match whole words only (case insensitive)
            response_text = re.sub(rf'\b{re.escape(member.display_name)}\b', f"<@{member.id}>", response_text, flags=re.IGNORECASE)
            response_text = re.sub(rf'\b{re.escape(member.name)}\b', f"<@{member.id}>", response_text, flags=re.IGNORECASE)

    return response_text
