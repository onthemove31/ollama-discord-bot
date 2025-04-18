# Ollama Discord Bot

This bot connects to an Ollama instance and allows interaction via Discord.

## Features
- Responds to messages in a designated channel.
- Streams Ollama replies.
- Displays typing indicator while processing.
- Sends inactivity messages to keep the channel active.
- **Role-Based Personas**: Users can set the bot to adopt different personalities.
- **Configurable GIF Responses**: Can send context-aware GIFs (optional).
- **Conversation History**: Maintains context within user conversations (configurable length).
- Uses `.gitignore` to protect sensitive files like `.env` and avoid committing unnecessary files.

## Setup

1.  **Clone the repository.**
2.  **Create a `.env` file** based on `.env.example` (if provided) or manually add the required variables:
    *   `DISCORD_BOT_TOKEN`: Your Discord bot token.
    *   `TARGET_CHANNEL_ID`: The ID of the Discord channel the bot should operate in.
    *   `ALLOWED_USER_IDS`: Comma-separated list of user IDs allowed to interact (optional).
    *   `OLLAMA_API_URL`: The base URL of your Ollama API (e.g., `http://localhost:11434`). The script specifically uses the `/api/chat` endpoint.
    *   `OLLAMA_MODEL_NAME`: The Ollama model to use (e.g., `dolphin-mistral:latest`).
    *   `SYSTEM_PROMPT`: The *default* system prompt if no role is set (used for the `sarcastic_therapist` role in the current config).
    *   `MAX_CONTEXT_LENGTH`: Max messages to keep in history per user.
    *   `INACTIVITY_THRESHOLD_HOURS`: Hours of inactivity before the bot sends a message.
    *   `GIF_FOLDER`: Path to the GIF category folders (optional).
    *   `GIF_CHANCE`: Probability (0.0 to 1.0) of sending a GIF (optional).
3.  **Install dependencies:** `pip install -r requirements.txt`
4.  **(Optional) Download GIFs:** If using the GIF feature, ensure the folders specified in `GIF_FOLDER` exist and contain GIFs. A helper script `download_gifs.py` might be available (requires `gif_downloader_requirements.txt`).

## Running the Bot

```bash
python ollama_discord_bot.py
```

## Commands

*   `/clear` or `!clear`: Clears your conversation history with the bot.
*   `/listroles` or `!listroles`: Shows the available bot personas you can set.
*   `/setrole <role_name>` or `!setrole <role_name>`: Sets the bot's persona for your future interactions. Example: `/setrole pirate`.
*   `/gif on` or `!gif on`: Enables automatic GIF responses for you.
*   `/gif off` or `!gif off`: Disables automatic GIF responses for you.
*   `/gif` or `!gif`: Sends a random GIF.

## Available Roles (Default: `sarcastic_therapist`)

*   `helpful_assistant`
*   `sarcastic_therapist`
*   `comedian`
*   `pirate`
*   `gojo`
*   `luffy`
*   `naruto`
*   `rajini`
*   `ajith`
*   `vijay`
*   `batman`
*   `catwoman`

(These are defined in the `BOT_ROLES` dictionary in the script).

## .gitignore

The `.gitignore` file is configured to exclude:
*   `.env` (Contains secrets)
*   Python cache files (`__pycache__/`, `*.pyc`)
*   `gamification_data.json`
*   `Dockerfile`
*   `download_gifs.py`
*   `gif_downloader_requirements.txt`
*   The `gifs/` directory

## How to Run (Docker on Unraid)

1. Edit `.env` file with correct values.

2. Build the Docker image: