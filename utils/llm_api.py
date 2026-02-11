import aiohttp
import json
import os
import config

# Optional: flip to True if you want file/module paths printed once at import time
DEBUG_IMPORTS = False
if DEBUG_IMPORTS:
    print("llm_api loaded from:", __file__)
    print("config loaded from:", getattr(config, "__file__", "unknown"))
    print("config.OPENWEBUI_API_URL =", repr(getattr(config, "OPENWEBUI_API_URL", None)))

async def query_llm(ctx, prompt: str, private_channel=None) -> str:
    """Send a request to the LLM API and return the generated response."""
    if not config.OPENWEBUI_API_URL or not config.OPENWEBUI_API_KEY:
        return "Error: OpenWebUI URL and/or API settings are missing."

    # Show typing indicator while waiting for the LLM response
    async with private_channel.typing() if private_channel else ctx.typing():
        headers = {
            "Authorization": f"Bearer {config.OPENWEBUI_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": config.MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(config.OPENWEBUI_API_URL, json=payload, headers=headers) as response:
                    if response.status == 200:
                        # Prefer JSON response
                        try:
                            json_data = await response.json()
                        except Exception:
                            raw = await response.text()
                            return f"Error: API returned non-JSON response: {raw}"

                        return (
                            json_data.get("choices", [{}])[0]
                            .get("message", {})
                            .get("content", "No response generated.")
                        )

                    # Non-200: include body safely (await text!)
                    err_text = await response.text()
                    return f"API Error: {response.status} - {err_text}"

        except aiohttp.ClientError as e:
            return f"Request Failed: {e}"
        except json.JSONDecodeError:
            return "Error: Failed to decode the response from the API."
        except Exception as e:
            return f"Unexpected error: {e}"

async def query_llm_with_command_info(command_info: dict, user_question: str, ctx, private_channel=None) -> str:
    """Process command-specific context and user question, then send to LLM."""
    llm_context = command_info.get("LLM_Context", "No additional context available.")
    example = command_info.get("Example", "No example available.")
    description = command_info.get("Description", "No description available.")

    # Load prompt templates from prompts.json (relative to project root)
    prompts_path = os.path.join("data", "prompts.json")
    try:
        with open(prompts_path, "r", encoding="utf-8") as file:
            prompts_data = json.load(file)
    except FileNotFoundError:
        return "Error: prompts.json file not found."
    except json.JSONDecodeError:
        return "Error: Failed to parse prompts.json file."

    prompt_template = prompts_data.get("help_detailed", {}).get("LLM_Message", "No prompt available.")

    prompt = prompt_template.format(
        Command_Name=command_info.get("Command_Name", "unknown"),
        LLM_Context=llm_context,
        Example=example,
        Description=description,
        USER_QUESTION=user_question,
        COMMAND_PREFIX=config.COMMAND_PREFIX,
        BOT_NAME=config.BOT_NAME,
    )

    return await query_llm(ctx, prompt, private_channel)

async def query_llm_with_prompt(prompt_name: str, ctx, private_channel=None) -> str:
    """
    Load a prompt by name from prompts.json and send it to the LLM server.
    """
    prompts_path = os.path.join("data", "prompts.json")
    try:
        with open(prompts_path, "r", encoding="utf-8") as file:
            prompts_data = json.load(file)
    except FileNotFoundError:
        return "Error: prompts.json file not found."
    except json.JSONDecodeError:
        return "Error: Failed to parse prompts.json file."

    prompt_message = prompts_data.get(prompt_name, {}).get("LLM_Message", "")
    if not prompt_message:
        return f"Error: No prompt found with the name '{prompt_name}'."

    return await query_llm(ctx, prompt_message, private_channel)

def load_commands():
    """Load command data from commands.json and return a dict keyed by command name."""
    commands_path = os.path.join("data", "commands.json")
    try:
        with open(commands_path, "r", encoding="utf-8") as file:
            return {cmd["Command_Name"].lower(): cmd for cmd in json.load(file)}
    except FileNotFoundError:
        return "Error: commands.json file not found."
    except json.JSONDecodeError:
        return "Error: Failed to parse commands.json file."
