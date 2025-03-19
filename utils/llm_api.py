import aiohttp
import json
import os

# Existing function - DO NOT CHANGE!
async def query_llm(ctx, prompt, private_channel=None):
    """Send a request to the LLM API and return the generated response with typing indicator."""
    if not OPENWEBUI_API_URL or not OPENWEBUI_API_KEY:
        return "Error: OpenWebUI URL and/or API settings are missing."

    # Show typing indicator while waiting for the LLM response in the private channel
    async with private_channel.typing() if private_channel else ctx.typing():
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

# NEW FUNCTION: Automatically loads prompt templates and sends the final prompt.
async def query_llm_with_template(ctx, prompt_name, llm_context, example, user_question, private_channel=None):
    """Load prompt template from data/prompts.json, build the final prompt, and query the LLM."""
    prompts_path = os.path.join("data", "prompts.json")
    try:
        with open(prompts_path, "r") as f:
            prompts = json.load(f)
    except Exception as e:
        return f"Error loading prompt templates: {e}"
    
    prompt_data = prompts.get(prompt_name)
    if prompt_data is None:
        # Fall back to "help_default" if the provided prompt name is not found.
        prompt_data = prompts.get("help_default", {
            "LLM_Message": "Context: {LLM_Context}\nExample: {Example}\nUser Question: {USER_QUESTION}"
        })
    llm_message_template = prompt_data.get("LLM_Message")
    
    final_prompt = llm_message_template.format(
        LLM_Context=llm_context,
        Example=example,
        USER_QUESTION=user_question
    )
    
    return await query_llm(ctx, final_prompt, private_channel=private_channel)
