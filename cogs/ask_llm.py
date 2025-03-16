import aiohttp
import asyncio
from config import OPENWEBUI_API_URL  # Define this in your config.py

async def query_llm(question: str) -> str:
    """
    Sends a question to Open WebUI and returns the response.
    Assumes Open WebUI API is running and accessible.
    """
    async with aiohttp.ClientSession() as session:
        try:
            # Adjust this URL to match your Open WebUI endpoint
            url = f"{OPENWEBUI_API_URL}/ask"
            
            # Prepare the data to send to the Open WebUI API
            data = {
                "question": question  # assuming 'question' is the expected field in Open WebUI
            }

            # Send the POST request to Open WebUI
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    response_json = await response.json()
                    # Assuming the response contains the answer in the 'answer' field
                    return response_json.get("answer", "No response from Open WebUI.")
                else:
                    return f"Error: Received status code {response.status}"
        except Exception as e:
            print(f"[ERROR] Failed to query Open WebUI: {e}")
            return f"An error occurred: {e}"
