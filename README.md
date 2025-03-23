# DiscordDevros

DiscordDevros is a Discord bot interconnected with an Open WebUI server to generate unique and more natural language responses. The code is structured in a modular format to allow for easy customization based on the needs of your server. The `cogs` folder contains the code for all commands available on the server. Each script is either an individual command, or a group of commands that function together to create a game or other feature. 

## Setting Up your Open WebUI Server:

## Setting up your Discord Bot:

## Installation

### 1. Clone the Repository

```sh
git clone git@github.com:GuamBoi/DiscordDevros.git
cd DiscordDevros
```

### 2. Set Up a Virtual Environment

Create a virtual environment to isolate the bot's dependencies:

```sh
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

Once the virtual environment is activated, install the required Python dependencies:

```sh
pip install -r requirements.txt
```

### 4. Setup Environment Variables and `config.py` file Variables

1. Create a `.env` file in the root directory and add your bot token and command prefix:

```bash
nano .env
```

```
DISCORD_BOT_TOKEN=YOUR_DISCORD_BOT_TOKEN
OPENWEBUI_API_URL=http://RASPBERRY_PI_IP:PORT/api/chat/completions
OPENWEBUI_API_KEY=YOUR_OPENWEBUI_API_KEY
```

2. Edit the `config.py` file to configure the bot to your server and liking:

```bash
nano config.py
```

```python
import os
from dotenv import load_dotenv

# Load environment variables from .env file.
load_dotenv()

# Sensitive settings (Change these in the .env file only)
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")     # Pulled from .env file
OPENWEBUI_API_KEY = os.getenv("OPENWEBUI_API_KEY")     # Pulled from .env file
OPENWEBUI_API_URL = os.getenv("OPENWEBUI_API_URL")     # Pulled from .env file

# Non-sensitive settings (Additional bot settings that are okay to share)
BOT_NAME = "YOUR_BOTS_NAME"          # The name of your bot
BOT_VERSION = "YOUR_VERSION_NUMBER"  # The version of your bot
COMMAND_PREFIX = "YOUR_PREFIX"       # Change value if you want different prefix.
MODEL_NAME = "YOUR_LLM_MODEL_NAME"   # Set your model name here.

# Server Economy Settings
ECONOMY_FOLDER = "eco"               # Folder where economy files are saved
CURRENCY_NAME = "CURRENCY_NAME"      # Name of your server's currency
CURRENCY_SYMBOL = "CURRENCY_SYMBOL"  # Symbol of your server's currency
DEFAULT_CURRENCY_GIVE = NUMBER_HERE          # Default value adding currency
DEFAULT_CURRENCY_TAKE = NUMBER_HERE          # Default value adding currency
GAME_WIN = NUMBER_HERE                       # Game win currency value
GAME_LOSE = NUMBER_HERE                      # Game lost currency value

# Channel Specifications (Defined directly in config.py, not from .env)
WORDLE_CHANNEL = WORDLE_CHANNEL_ID         # Set your Wordle Game Channel
INVITE_CHANNEL = INVITE_CHANNEL_ID         # Set your Game Invite Channel ID
WELCOME_CHANNEL = WELCOME_CHANNEL_ID        # Set your Welcome Channel ID
GOODBYE_CHANNEL = GOODBYE_CHANNEL_ID        # Set your Goodbye Channel ID
BETTING_CHANNEL = BETTING_CHANNEL_ID        # Set your Betting Channel ID
HELP_COMMAND_CHANNEL_CATEGORY = HELP_COMMAND_CATEGORY_ID
ROLLS_CHANNEL = BETTING_CHANNEL_ID          # Set Roll Selection Channel ID
```

### 5. Update the `rolls.json` File to Match Your Server
```json
{
    "color": {
        "message": "Server Color Selection",
        "description": "Color Key:",
        "note": "Pick 1 color at a time.",
        "options": {
            "YOUR_ROLL_EMOJI": {"name": "`YOUR_ROLL_NAME`", "role_id": YOUR_ROLL_ID},
            "YOUR_ROLL_EMOJI": {"name": "`YOUR_ROLL_NAME`", "role_id": YOUR_ROLL_ID},
        }
    },
    "game": {
        "message": "Game Selection",
        "description": "Server Game Options:",
        "note": "Select all the games you want to be a part of!",
        "options": {
            "YOUR_ROLL_EMOJI": {"name": "`YOUR_ROLL_NAME`", "role_id": YOUR_ROLL_ID},
            "YOUR_ROLL_EMOJI": {"name": "`YOUR_ROLL_NAME`", "role_id": YOUR_ROLL_ID},
        }
    },
    "free_game": {
        "message": "Free Game and Update Channels",
        "description": "Channel Options:",
        "note": "Game update channel selection.",
        "options": {
            "YOUR_ROLL_EMOJI": {"name": "`YOUR_ROLL_NAME`", "role_id": YOUR_ROLL_ID},
            "YOUR_ROLL_EMOJI": {"name": "`YOUR_ROLL_NAME`", "role_id": YOUR_ROLL_ID}
        }
    }
}
```

### 6. Test the Bot

After setting up the environment, test the bot and try some of the commands after running the following command:

```sh
python bot.py
```

After you test everything ensure your Discord bot continues running after you close your SSH session, you can utilize the `nohup` command. This command allows processes to persist even after your PuTTY session is closed. Close your current PuTTY instance and run the following commands after you log back in:

### 7. Run the Bot Using `nohup`

Enter the Bot Directory and activate the virtual environment again

```bash
cd DiscordDevros
source venv/bin/activate
```

To run your bot so that it continues operating after you disconnect from the SSH session, use the `nohup` command:

```bash
nohup python bot.py > bot_output.log 2>&1 &
```

In this command:
- `nohup` prevents the process from being terminated after the SSH session ends.
- `python bot.py` executes your bot script.
- `> bot_output.log` redirects the standard output to a log file named `bot_output.log`.
- `2>&1` ensures that both standard output and standard error are captured in the log file.
- `&` runs the process in the background, allowing you to continue using the terminal.

**2. Verify the Bot is Running**

To confirm that your bot is running in the background, you can check the list of running processes:

```bash
ps aux | grep bot.py
```

This command will display information about the running `bot.py` process.

**Example PID Output:**

```
USER    PID   %CPU  %MEM   VSZ   RSS   TTY     STAT   START   TIME  COMMAND
guam   3132   5.2   4.4  198864 41772  pts/0    Sl    01:45   0:01  python bot.py
```

### Stopping the Bot 
- If you need to stop the bot, first identify its Process ID (PID) using the`ps aux | grep bot.py` command, then terminate it:
	
```bash
kill PID
```
	
- **Viewing Logs**: To monitor the bot's output, you can view the log file:
    
```bash
tail -f bot_output.log
```
   
This command will display the log content in real-time.

### Removing the Bot

```bash
sudo chown -R $USER:$USER ~/DiscordDevros
rm -rf ~/DiscordDevros
```

## Adding Commands

To add a new command, create a `.py` file in the `cogs/` folder and follow this structure:

#### Example Command

```python
from discord.ext import commands

class Example(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx):
        await ctx.send("Hello, world!")

async def setup(bot):
    await bot.add_cog(Example(bot))
```

#### Example command to ping the Open WebUI Server with a prompt

```python
from discord.ext import commands
from utils.llm_api import query_llm  # Import the query_llm function

class Example(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx, *, prompt: str = "Say Hello to the server and inttroduce yourself"):
        """Command to ask the LLM with a customizable prompt."""
        try:
            # Ask the LLM with the user-defined prompt or default if not provided
            response = await query_llm(prompt)
            await ctx.send(response)  # Send the LLM's response to Discord
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

async def setup(bot):
    await bot.add_cog(Example(bot))
```

#### Adding Commands to the `commands.json` file

```json
    {
        "Command_Name": "",
        "Description": "",
        "Example": "",
        "LLM_Context": ""
    }
```

## File Structure

```markdown
DiscordDevros/         # Main Directory
│
├── cogs/                 # Folder for command files
│   ├── __init__.py          # Makes the cogs folder a package
│   ├── ask.py               # Ask your Pi LLM a question (Ai)
│   ├── bet.py               # Handles bets between 2 server members
│   ├── command_help.py      # Starts a chat to help users with commands (Ai)
│   ├── dice.py              # Allows users to roll diffrent DND dice
│   ├── invite.py            # Sends a game invite to the game being played
│   ├── leaderboard.py       # Allows Users to check the economy leaderboard
│   ├── server_customization.py  
│   └── wordle.py            # Commands for starting / guessing in wordle (Ai)
│
├── data/                 # Folder for storing 
│   ├── commands.json        # File for storing command descriptions
│   ├── prompts.json         # File for configuring Ai Message
│   ├── rolls.json           # File for configuring server rolls
│   └── wordle_words.txt     # File that lists backup wordle words
│
├── utils/                # Folder for utility script function files
│   ├── __init__.py          # Makes the utils folder a package
│   ├── dictionary.py        # Loads and formats command information
│   ├── economy.py           # Handls the economy logic
│   ├── embed.py             # Handles the embed format for bot messages
│   └── llm_api.py           # Handles connection with Open WebUI's API
│
├── .env                     # Stores bot token, prefix, and API info
├── .gitignore               # Ignores sensitive files when cloned
├── README.md                # Code documentation (This File)
├── bot.py                   # Main bot file (loads commands dynamically)
├── config.py                # Cofiguration file for bot settings
└── requirements.txt         # Dependencies that need to be installed
````

___

## **cogs/** Command Code Files Explained

#### **ask.py**
The `ask` command allows users to ask an AI (via Open WebUI) any question and receive a response in the form of a well-formatted embed. The bot sends the user's question to the AI, processes the response, and sends it back in a clean, readable format. Here's a step-by-step breakdown of how this command works:

1. **User Interaction**:  
    When a user types `!ask <question>`, the command is triggered. The user’s question is passed as the `question` argument to the bot.
    
2. **Handling the Question**:  
    The question is passed to the `query_llm` function in the `llm_api.py` file. This function is responsible for interacting with the Open WebUI API and sending the question to the AI model. It also ensures that the typing indicator appears while the model is processing the request.
    
    - **Typing Indicator**: The `ctx` (context) is passed to `query_llm` to show the typing indicator while the AI processes the question. This helps indicate to the user that the bot is working on generating a response.
	
3. **Generating the Response**:  
    Once the AI generates a response, the `query_llm` function returns the result as a string. This response is then formatted into an embed using the `create_embed` function, which is defined in `embed.py`. The embed contains:
    
    - **Title**: `"Response:"`
    - **Description**: The AI’s generated response.
    - **Footer**: `"Message generated by AI"`, indicating the source of the response.
	
4. **Sending the Response**:  
    After creating the embed, the bot sends the formatted response back to the Discord channel using `ctx.send(embed=embed)`. The embed is sent without pinging the original user, keeping the message clean and professional.
    
5. **Error Handling**:  
    If an error occurs at any point (such as a failure to connect to the Open WebUI server or an issue with formatting), the bot catches the exception. The bot then generates an error embed to inform the user. The error embed is formatted similarly to the response embed but has the following differences:
    
    - **Title**: `"❌ Error"`
    - **Description**: The error message, which is provided by the exception (`{e}`).
    - **Color**: The embed has a red color to signify that an error occurred.
    - **Footer**: `"Message generated by AI"` to maintain consistency.
    
    The error embed is sent back to the channel, ensuring the user is informed about the issue.
    
6. **`create_embed`**:  
    The `create_embed` function is an asynchronous function defined in `embed.py`. It is responsible for constructing the embed with the appropriate title, description, footer, and any optional formatting such as color.
    
7. **Cog Structure**:  
    The `ask` command is part of the `AskLLMCog` class, which is a cog that encapsulates the functionality related to asking the AI model. The cog is added to the bot through the `setup` function, which is required to be asynchronous in order to properly load the cog.
    
8. **Result**:  
    Once the AI response is generated and formatted into an embed, the bot sends the embed to the Discord channel, providing a clean response to the user's question. If an error occurs, the bot sends an error embed to notify the user of the issue.
    

Overall, the `ask` command provides a seamless way for users to interact with the AI model, ask questions, and receive intelligent, AI-generated responses in a visually appealing format.

___

#### **command_help.py**
The `command_help` command allows users to get detailed information about specific bot commands or see a list of all available commands. Here's how it works and how it uses supporting files:

1. **User Interaction**:  
    When a user types `!command_help <command_name>`, the bot checks if the given command exists in the `commands.json` file. If no command name is provided, it lists all available commands.
    
2. **commands.json**:  
    This file contains structured data for each command, including its name, description, example usage, and context for the AI. The bot uses this data to retrieve relevant information about the command specified by the user.
    
3. **prompts.json**:  
    This file contains templates for how the bot should frame its responses when providing detailed information. It includes placeholders like `{Command_Name}`, `{Example}`, and `{USER_QUESTION}`. The `query_llm_with_command_info` function reads the appropriate template and replaces these placeholders with actual values from `commands.json`.
    
4. **llm_api.py**:  
    After the prompt is generated using the data from `commands.json` and `prompts.json`, the `query_llm_with_command_info` function sends the formatted prompt to the AI server using the `query_llm` function. The AI then generates a response, which is sent back to the user in a private chat.
    
5. **Result**:  
    If the AI server responds successfully, the bot sends the detailed explanation to the user. If there’s an error (e.g., command not found or server issue), an appropriate error message is returned.
    

Overall, `command_help` provides users with personalized, AI-generated explanations about how to use the bot's commands, using structured data and adaptable response templates.

___

#### **server_customization.py**

The `server_customization.py` file is a cog for the Discord bot that enables server administrators to easily customize and manage role reactions for users. This feature allows users to select roles via reaction emojis on embedded messages that the bot sends to a specific channel. The bot then handles adding and removing roles based on those reactions, making it easy to offer dynamic roles (such as color roles, notification preferences, and channel access) to users.

**Key Features:**

1. **Role-based Reactions:** The bot sends multiple embed messages to a specified channel, each representing a different category of roles (color roles, channel roles, and notification preferences). Users can react to these messages with specific emojis, and the bot will assign or remove the corresponding roles.
    
2. **Persistent Role Data:** Role configuration data (such as role names, emojis, and descriptions) is stored in a JSON file (`rolls.json`). This data can be updated without restarting the bot, and it allows for easy addition or removal of roles and emojis.
    
3. **Automatic Role Assignment and Removal:** When a user reacts to an embed message, the bot checks which role corresponds to the selected emoji and then assigns that role to the user. Similarly, when a user removes their reaction, the bot removes the corresponding role from the user.
    
4. **Customizable Embed Messages:** The embed messages sent by the bot can be customized for each category of roles. The bot will generate a unique embed with a description of the roles and corresponding emojis for each category (color, channels, notifications).
    
5. **Persistence Across Restarts:** The `server_customization.py` file ensures that the roles and reactions remain persistent, even when the bot is restarted. This is accomplished by saving the message IDs and reactions in a JSON file (`message_ids.json`) so the bot can re-add the reactions to the correct messages when it starts back up.
 
**How to Use:**

1. **Run the `!server_customization` Command:** When you run the `!server_customization` command, the bot will send three embed messages (one for each category of roles: color, channels, notifications) to the specified channel. Each embed will list the available roles and emojis that users can react to.
    
2. **React to Embed Messages:** Users can react to the embed messages with the corresponding emojis to select their roles. Once a user reacts, the bot will automatically assign the corresponding role to them.
    
3. **Reacting to Remove Roles:** Users can also remove roles by clicking the corresponding emoji again to remove their reaction, and the bot will remove the assigned role.
    
4. **Customizing Roles:** Server admins can customize the roles and emojis by modifying the `rolls.json` file. This file stores all the configuration data for the roles, including the role names, emojis, and descriptions.
   
___

## **data/** Bot Data Files Explained
#### **commands.json**

A `.json` file that provides the bot with information about the different commands for the bot.

#### **prompts.json**

A `.json` file used to send customizable prompts to the Open WebUI LLM. 

#### **rolls.json**

A `.json` file used to dynamically update the `server_customization.py` file embeds for managing server rolls on the server.

## **utils/** Utility Functions Explained Explained

#### **llm_api.py**

The `llm_api.py` file contains functions to interact with Open WebUI’s API, facilitating communication between the bot and the AI model. There are three main functions in this file:

1. **`query_llm(ctx, prompt: str, private_channel=None)`**  
    This function sends a query (in the form of a prompt) to the Open WebUI API, processes the response, and returns the AI-generated output. It also manages the typing indicator while waiting for the response.
    
    **Steps**:
    
    - The `prompt` parameter contains the question or command that the user sends to the AI.
    - The `ctx` parameter represents the context for the interaction (such as a Discord context), and it’s used to display typing indicators to inform the user that the bot is processing their request.
    - The `private_channel` parameter is optional and allows showing typing activity in a private channel.
    - The function constructs a POST request with the `prompt`, API key, and necessary headers to communicate with the Open WebUI API.
    - The response from the API is parsed, and the AI-generated message is extracted from the response JSON.
    - The result is returned to the caller, typically to be sent back to the user in a Discord message.
    
    This function ensures that the bot can send prompts to the AI and return relevant responses dynamically to the user.

2. **`query_llm_with_command_info(command_info, user_question, ctx, private_channel=None)`**  
    This function processes command-specific context and user input, constructs a prompt using data from the `commands.json` file, and sends it to the Open WebUI API. It’s primarily used for generating help responses or detailed instructions for specific commands.
    
    **Steps**:
    
    - The `command_info` parameter contains the command-related data (e.g., name, description, example usage) that is fetched from the `commands.json` file.
    - The `user_question` parameter is the specific question or additional context the user provides.
    - The function extracts relevant command details (context, example, and description) from `command_info`.
    - It then loads the appropriate prompt template from `prompts.json`, replacing placeholders with the actual command details and the user's question.
    - This formatted prompt is sent to the Open WebUI API for processing.
    - The AI processes the prompt and returns a tailored response, which is sent back to the user.

    This function is designed to handle requests for command-specific help, dynamically generating detailed responses based on the data for each command.

3. **`query_llm_with_prompt(prompt_name, ctx, private_channel=None)`**  
    This function loads a predefined prompt by name from the `prompts.json` file, formats it, and sends it to the Open WebUI API to get a response based on the specified prompt template.
    
    **Steps**:
    
    - The `prompt_name` parameter specifies the name of the prompt template to be used, which is loaded from the `prompts.json` file.
    - The function fetches the corresponding prompt template and formats it, if necessary, with additional dynamic content (like user input or context).
    - This formatted prompt is then sent to the Open WebUI API to generate a response.
    - The AI’s output is returned to the caller, often for further processing or direct delivery to the user.

    This function allows for easy querying of predefined prompts that are stored in `prompts.json`, providing flexibility in how the bot interacts with the AI.

These three functions together enable the bot to dynamically query the AI model, process various types of requests (such as general queries or command-specific help), and return informative, context-aware responses to the user.

___

#### **economy.py**

The `economy.py` file contains the logic for managing the economy system within your Discord server, including handling user balances, transactions, and server-wide economic features like currency and leaderboards. This file interacts with the configuration defined in `config.py` to manage the server's economy and allows for easy customization.

###### **Features:**

- **Currency Management**:  
    The system provides functionality for awarding, removing, and checking user balances, as well as managing the server's currency type.
    
- **File Storage**:  
    All economy-related data is stored in files within the folder specified by `ECONOMY_FOLDER` in `config.py`. This ensures that user data persists even after the bot is restarted.
    
- **Economy Transactions**:  
    Users can earn or spend currency through bot commands, such as `bet.py`. These transactions are reflected in the user's balance and saved incase the bot crashes.

###### **Configuration:**

Economy-related settings are defined in `config.py` under the **Server Economy Settings** section:

```python
# Server Economy Settings
ECONOMY_FOLDER = "YOUR_ECONOMY_FOLDER_NAME"  # Folder where economy files save
CURRENCY_NAME = "YOUR_$_NAME"                # Name of your server's currency
DEFAULT_CURRENCY_GIVE = NUMBER_HERE          # Default value adding currency
DEFAULT_CURRENCY_TAKE = NUMBER_HERE          # Default value adding currency
```

- `ECONOMY_FOLDER`: Specifies where the economy files will be saved (e.g., user balances).
- `CURRENCY_NAME`: Defines the name of your server's currency (e.g., "coins", "gold").
- `DEFAULT_CURRENCY_GIVE`: The default amount of currency given to new users or upon certain actions.
- `DEFAULT_CURRENCY_TAKE`: The default amount of currency deducted in specific commands or actions.
