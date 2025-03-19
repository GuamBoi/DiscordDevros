import aiohttp
from config import OPENWEBUI_API_URL, OPENWEBUI_API_KEY, MODEL_NAME, COMMAND_PREFIX

async def query_llm(ctx, prompt, private_channel=None):
    """Send a request to the LLM API and return the generated response with typing indicator."""
    if not OPENWEBUI_API_URL or not OPENWEBUI_API_KEY:
        return "Error: OpenWebUI URL and/or API settings are missing."

    # Show typing indicator while waiting for the LLM response
    async with private_channel.typing() if private_channel else ctx.typing():
        headers = {
            'Authorization': f'Bearer {OPENWEBUI_API_KEY}',
            'Content-Type': 'application/json'
        }

        data = {
            "model": MODEL_NAME,
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
                        return response_text
                    else:
                        return f"API Error: {response.status}"
        except Exception as e:
            return f"Request Failed: {e}"

async def query_llm_with_command_info(ctx, prompt_name, llm_context, example, user_question, private_channel=None):
    """Send a request to the LLM API using command information from prompts.json."""
    from utils.prompts import load_prompts

    prompts = load_prompts()
    prompt_data = prompts.get(prompt_name)

    if not prompt_data:
        # Fallback to help_default if prompt not found
        prompt_data = prompts.get("help_default", {
            "LLM_Message": "Context: {LLM_Context}\nExample: {Example}\nUser Question: {USER_QUESTION}"
        })

    llm_message_template = prompt_data.get("LLM_Message")

    # Format the prompt using available variables
    final_prompt = llm_message_template.format(
        LLM_Context=llm_context,
        Example=example,
        USER_QUESTION=user_question,
        COMMAND_PREFIX=COMMAND_PREFIX
    )

    return await query_llm(ctx, final_prompt, private_channel=private_channel)
