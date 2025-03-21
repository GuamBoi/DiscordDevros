import aiohttp
import json
from utils.embed import create_embed  # Import the create_embed function from utils/embed.py
from config import OPENWEBUI_API_KEY, OPENWEBUI_API_URL, MODEL_NAME, BOT_NAME, COMMAND_PREFIX

async def query_llm(ctx, prompt, private_channel=None):
    """Send a request to the LLM API and return the generated response."""
    if not OPENWEBUI_API_URL or not OPENWEBUI_API_KEY:
        return "Error: OpenWebUI URL and/or API settings are missing."

    # Show typing indicator while waiting for the LLM response in the private channel
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
            # Open session for making the request
            async with aiohttp.ClientSession() as session:
                async with session.post(OPENWEBUI_API_URL, json=data, headers=headers) as response:
                    # Check response status
                    if response.status == 200:
                        json_data = await response.json()
                        response_text = json_data.get("choices", [{}])[0].get("message", {}).get("content", "No response generated.")
                        return response_text
                    else:
                        return f"API Error: {response.status}"
        except Exception as e:
            return f"Request Failed: {e}"

async def query_llm_with_command_info(command_info, user_question, ctx, private_channel=None):
    """Process command-specific context and user question, then send to LLM."""
    # Extract relevant data (LLM context, example, description) for the command
    llm_context = command_info.get("LLM_Context", "No additional context available.")
    example = command_info.get("Example", "No example available.")
    description = command_info.get("Description", "No description available.")

    # Load prompt templates from prompts.json
    with open('data/prompts.json', 'r') as file:
        prompts_data = json.load(file)

    # Use the 'help_detailed' template by default
    prompt_template = prompts_data.get("help_detailed", {}).get("LLM_Message", "No prompt available.")

    # Replace placeholders with actual values
    prompt = prompt_template.format(
        Command_Name=command_info['Command_Name'],
        LLM_Context=llm_context,
        Example=example,
        USER_QUESTION=user_question,
        COMMAND_PREFIX=COMMAND_PREFIX,
        BOT_NAME=BOT_NAME
    )

    # Get the LLM response
    response_text = await query_llm(ctx, prompt, private_channel)

    # Use the `create_embed` function from utils/embed.py to create the embed
    embed = await create_embed(
        title=f"Help for Command: {command_info['Command_Name']}",
        description=response_text,
        footer_text=f"{command_info['Command_Name']} - Help",
    )

    # Add additional fields to the embed for description and example
    embed.add_field(name="Description", value=description, inline=False)
    embed.add_field(name="Example", value=example, inline=False)

    # Send the embed in the channel
    await ctx.send(embed=embed)

    return response_text

def load_commands():
    """Function to load command data from the commands.json file."""
    with open('data/commands.json', 'r') as file:
        return {cmd['Command_Name'].lower(): cmd for cmd in json.load(file)}
