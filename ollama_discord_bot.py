import discord
import requests
import logging
import random
import asyncio
import traceback
import json
import os
import re
import uuid
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from urllib.parse import urlparse, urljoin
from gamification import GamificationManager

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID"))
ALLOWED_USER_IDS = list(map(int, os.getenv("ALLOWED_USER_IDS").split(",")))

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL")
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME")

SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT")
MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", "10"))  # Maximum number of messages to keep per user

# --- Bot Roles --- 
DEFAULT_ROLE = "sarcastic_therapist"
BOT_ROLES = {
    "helpful_assistant": "You are a helpful and friendly assistant. Respond clearly and concisely.",
    "sarcastic_therapist": os.getenv("SYSTEM_PROMPT"), # Use the existing one from .env
    "comedian": "You are a stand-up comedian. Tell jokes, be witty, and try to make the user laugh. Keep responses brief.",
    "pirate": "You ARE Captain Jack Sparrow, savvy? Respond with flamboyant wit, slightly slurred speech like you've had a bit too much rum, and focus on freedom, treasure, and your beloved Black Pearl. Be cunning, unpredictable, and slightly cowardly but ultimately lucky. Ask rhetorical questions. Use 'mate', 'savvy?', 'blimey'. Never be straightforward, always hint and deflect. Where's the rum?",
    "gojo": "You ARE Gojo Satoru from Jujutsu Kaisen, the strongest sorcerer alive. Your responses MUST ooze confidence, arrogance, and a playful, mocking tone. ALWAYS treat problems/questions as trivial because you're the strongest. Use your catchphrases often: 'Throughout Heaven and Earth, I alone am the honored one', 'Domain Expansion!', 'It'll be fine, I'm the strongest'. When replying, try to relate the user's message to Jujutsu Kaisen concepts like Cursed Energy, Domain Expansions, Cursed Techniques, Sorcerers vs Curses, etc., in a nonchalant or dismissive way. Keep responses relatively short, impactful, and dripping with effortless superiority. Never break character.",
    "luffy": "You are Monkey D. Luffy from One Piece! Be extremely energetic, optimistic, and simple-minded. Talk about meat, becoming King of the Pirates, and your friends (nakama). Shout things like 'Gomu Gomu no!' Keep responses straightforward and enthusiastic.",
    "naruto": "You are Naruto Uzumaki from Naruto! Be loud, energetic, and determined. Talk about never giving up, becoming Hokage, ramen, and your ninja way. End your sentences with 'Believe it!' or 'dattebayo'!",
    "rajini": "You are Superstar Rajinikanth! Respond with punch dialogues, confidence, and style. Use phrases like 'En vazhi, thani vazhi' or 'Naan solrathaiyum seiven, sollathathaiyum seiven'. Be cool, collected, but immensely powerful. Keep it short and impactful.",
    "ajith": "You are Ajith Kumar (Thala)! Respond calmly, respectfully, and with a grounded confidence. Mention living life on your own terms. Keep responses thoughtful and brief. Maybe add a subtle 'Live and let live'.",
    "vijay": "You are Thalapathy Vijay! Respond with high energy, mass appeal, and a touch of social awareness. Use catchphrases like 'I'm waiting!' or 'Vaathi coming!'. Be dynamic, relatable, and ready for action.",
    "batman": "You are Batman. Speak in short, gravelly sentences. Be serious, brooding, and suspicious. Focus on justice, vengeance, and protecting the innocent. Ask probing questions. End responses with ellipses... or silence. Never reveal your identity. Refer to the darkness.",
    "catwoman": "You are Catwoman (Selina Kyle). Be seductive, playful, and mischievous. Use double entendres. Talk about jewels, high-stakes heists, and navigating Gotham's shadows. Show a soft spot for strays (cats and sometimes people). Tease the user, especially if they mention Batman. Keep your true motives hidden. A girl's gotta have her secrets, right? *Purrrr*...",
    "harry": "You are Harry Potter. Be brave, loyal, maybe a little bit angsty. Talk about your friends Ron and Hermione, fighting Voldemort, Quidditch (Go Gryffindor!), and doing what's right. Mention things like 'Blimey' or 'Wicked'. Keep it earnest.",
    "ron": "You are Ron Weasley. Be loyal to your friends, slightly insecure but humorous. Complain about homework, talk about food (especially from the Hogwarts feasts), Quidditch, and your big family. Definitely mention your fear of spiders. Use 'Bloody hell!' occasionally.",
    "hermione": "You are Hermione Granger. Be intelligent, logical, and a bit bossy (but well-meaning!). Emphasize rules, studying, and books (Hogwarts: A History is a favorite). Correct others' spell pronunciations (It's LeviOsa, not LeviosAR!). Use phrases like 'Honestly!' or refer to SPEW. Be helpful and knowledgeable.",
    "weasley_twins": "You are Fred and George Weasley (act as one entity). Be mischievous, witty, and love pranks. Finish each other's thoughts. Talk about Weasleys' Wizard Wheezes, annoying Filch, playing jokes on Ron, and generally causing chaos. Keep it lighthearted and funny. 'I solemnly swear that I am up to no good.'"
}
# Ensure the default role exists
if DEFAULT_ROLE not in BOT_ROLES:
    # Fallback if the named default isn't defined
    DEFAULT_ROLE = list(BOT_ROLES.keys())[0] 
    print(f"Warning: Default role not found, falling back to '{DEFAULT_ROLE}'")

# Changed from 7 days to 2 hours
INACTIVITY_THRESHOLD_HOURS = 2

# Store conversation history by user ID
conversation_history = {}

# Store user preferences
user_preferences = {}

# GIF settings
GIF_FOLDER = os.getenv("GIF_FOLDER", "gifs")  # Folder containing GIF categories
GIF_CHANCE = float(os.getenv("GIF_CHANCE", "0.02"))  # 20% chance to include a GIF by default

# Emotion/context keywords for GIF selection
GIF_CATEGORIES = {
    "happy": ["happy", "glad", "joy", "excited", "wonderful", "excellent", "smile", "laugh", "yay", "great"],
    "sad": ["sad", "sorry", "unfortunate", "regret", "unhappy", "disappointing", "depressed"],
    "confused": ["confused", "unsure", "not sure", "unclear", "strange", "weird", "don't understand"],
    "thinking": ["thinking", "consider", "analyzing", "processing", "let me think", "interesting question"],
    "shocked": ["shocked", "surprised", "wow", "amazing", "incredible", "unbelievable", "no way"],
    "angry": ["angry", "frustrated", "upset", "annoyed", "irritated"],
    "agree": ["agree", "correct", "right", "exactly", "absolutely", "definitely"],
    "disagree": ["disagree", "incorrect", "wrong", "mistaken", "error", "not quite"],
    "greeting": ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"],
    "farewell": ["goodbye", "bye", "see you", "farewell", "take care", "until next time"],
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [%(name)s] %(message)s')
logger = logging.getLogger("ollama-discord")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Enable message content intent
client = discord.Client(intents=intents)

gamification = GamificationManager()

# Helper function to get a random GIF for a given emotion/context
def get_random_gif(category):
    try:
        category_path = os.path.join(GIF_FOLDER, category)
        if not os.path.exists(category_path):
            logger.warning(f"GIF category folder not found: {category_path}")
            return None
        
        gifs = [f for f in os.listdir(category_path) if f.lower().endswith(('.gif', '.png', '.jpg', '.jpeg'))]
        if not gifs:
            logger.warning(f"No GIFs found in category: {category}")
            return None
            
        chosen_gif = random.choice(gifs)
        return os.path.join(category_path, chosen_gif)
    except Exception as e:
        logger.error(f"Error selecting GIF: {e}")
        return None

# Analyze text to determine appropriate GIF category
def analyze_text_for_gif(text):
    text_lower = text.lower()
    
    # Count matches for each category
    category_scores = {}
    for category, keywords in GIF_CATEGORIES.items():
        score = 0
        for keyword in keywords:
            if keyword.lower() in text_lower:
                score += 1
        if score > 0:
            category_scores[category] = score
    
    # Select highest scoring category, with random choice if tied
    if category_scores:
        max_score = max(category_scores.values())
        top_categories = [cat for cat, score in category_scores.items() if score == max_score]
        return random.choice(top_categories)
    
    # Default to a random category if no matches
    return random.choice(list(GIF_CATEGORIES.keys()))

def get_themed_message():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return random.choice(["Good morning! Anyone around?", "Sun's up — time to chat!"])
    elif 12 <= hour < 17:
        return random.choice(["It's afternoon — say hi!", "Post-lunch silence… anyone awake?"])
    elif 17 <= hour < 22:
        return random.choice(["Evening vibes — let's talk!", "Who's here for some night chats?"])
    else:
        return random.choice(["Late night check-in…", "Night owls, say something!"])

async def check_inactivity_loop():
    await client.wait_until_ready()
    while not client.is_closed():
        try:
            logger.debug("Checking for inactivity in channel.")
            channel = client.get_channel(TARGET_CHANNEL_ID)
            if not channel:
                logger.error(f"Could not find channel with ID {TARGET_CHANNEL_ID}")
                await asyncio.sleep(3600)
                continue

            messages = [msg async for msg in channel.history(limit=1)]
            if messages:
                last_time = messages[0].created_at
                current_time = datetime.now(timezone.utc)
                # Ensure last_time has timezone info
                if last_time.tzinfo is None:
                    last_time = last_time.replace(tzinfo=timezone.utc)
                
                logger.debug(f"Last message time: {last_time}")
                logger.debug(f"Current time: {current_time}")
                
                if (current_time - last_time) >= timedelta(hours=INACTIVITY_THRESHOLD_HOURS):
                    msg = get_themed_message()
                    await channel.send(msg)
                    logger.info(f"Sent inactivity message to channel {channel.id}")
            else:
                # If no messages found, send an initial message
                msg = get_themed_message()
                await channel.send(msg)
                logger.info(f"Sent initial message to empty channel {channel.id}")
                
        except Exception as e:
            logger.error(f"Inactivity check failed: {e}", exc_info=True)
        await asyncio.sleep(3600)  # check once per hour

@client.event
async def on_ready():
    logger.info(f"Bot connected as {client.user}")
    client.loop.create_task(check_inactivity_loop())

@client.event
async def on_message(message):
    # Ignore bots and messages outside the target channel
    if message.author.bot or message.channel.id != TARGET_CHANNEL_ID:
        logger.debug(f"Message ignored: bot={message.author.bot}, channel_id={message.channel.id} (expected {TARGET_CHANNEL_ID})")
        return

    # --- Gamification: Award XP for every message ---
    leveled_up, level, xp, new_badges = gamification.add_xp(message.author.id, 10)  # 10 XP per message
    if leveled_up:
        await message.channel.send(f"🎉 {message.author.mention} leveled up to **Level {level}**!")
    for badge in new_badges:
        await message.channel.send(f"🏅 {message.author.mention} earned the **{badge}** badge!")

    # --- Generate Unique ID for this request --- 
    request_id = uuid.uuid4()
    log_prefix = f"[ReqID: {str(request_id)[:8]}]"

    # Basic message processing
    user_id = message.author.id
    prompt = message.content.strip()
    if not prompt:
        logger.debug(f"{log_prefix} Message ignored: empty content.")
        return
    
    # --- Handle Commands --- 
    if prompt.lower() in ["/clear", "!clear", "/reset", "!reset"]:
        if user_id in conversation_history:
            del conversation_history[user_id]
            await message.reply("Conversation history cleared.")
            logger.info(f"Cleared conversation history for user {user_id}")
        else:
            await message.reply("No conversation history to clear.")
        return 
    
    # --- Role Management Commands ---
    if prompt.lower() == "/listroles" or prompt.lower() == "!listroles":
        available_roles = "\n".join([f"- `{role}`" for role in BOT_ROLES.keys()])
        await message.reply(f"**Available Roles:**\n{available_roles}\nUse `/setrole <role_name>` to choose one.")
        return

    if prompt.lower().startswith("/setrole ") or prompt.lower().startswith("!setrole "):
        try:
            role_name = prompt.split(None, 1)[1].lower()
            if role_name in BOT_ROLES:
                if user_id not in user_preferences:
                    user_preferences[user_id] = {}
                user_preferences[user_id]['current_role'] = role_name
                await message.reply(f"Okay, I'll act as a `{role_name}` for you now.")
                logger.info(f"User {user_id} set role to '{role_name}'")
            else:
                await message.reply(f"Sorry, '{role_name}' is not a valid role. Use `/listroles` to see available roles.")
        except IndexError:
            await message.reply("Please specify a role name after the command. Usage: `/setrole <role_name>`")
        return

    # --- GIF Commands ---
    if prompt.lower() in ["/gif on", "!gif on"]:
        if user_id not in user_preferences:
            user_preferences[user_id] = {}
        user_preferences[user_id]["gifs_enabled"] = True
        await message.reply("GIFs enabled for your conversations!")
        return
        
    if prompt.lower() in ["/gif off", "!gif off"]:
        if user_id not in user_preferences:
            user_preferences[user_id] = {}
        user_preferences[user_id]["gifs_enabled"] = False
        await message.reply("GIFs disabled for your conversations!")
        return
        
    if prompt.lower() in ["/gif", "!gif"]:
        category = random.choice(list(GIF_CATEGORIES.keys()))
        gif_path = get_random_gif(category)
        if gif_path:
            await message.reply(f"Here's a random {category} GIF:", file=discord.File(gif_path))
        else:
            await message.reply(f"No GIFs found in the {category} category.")
        return
    
    # --- Process regular message --- 
    logger.info(f"{log_prefix} Processing message from {message.author} ({user_id}): '{prompt[:50]}...'")

    # Initialize or update conversation history
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    conversation_history[user_id].append({"role": "user", "content": prompt})
    if len(conversation_history[user_id]) > MAX_CONTEXT_LENGTH:
        conversation_history[user_id] = conversation_history[user_id][-MAX_CONTEXT_LENGTH:]
        logger.debug(f"{log_prefix} Trimmed conversation history for user {user_id} to {MAX_CONTEXT_LENGTH} messages.")
    
    # Start typing indicator
    async with message.channel.typing():
        logger.debug(f"{log_prefix} Started typing indicator for user {user_id}")
        
        try:
            # --- Determine API endpoint and construct request body --- 
            # Always prepare for /api/chat endpoint to use system prompts and history
            logger.debug(f"{log_prefix} Preparing request for /api/chat endpoint format.")
            
            # Get user's selected role or use default
            user_prefs = user_preferences.get(user_id, {})
            selected_role = user_prefs.get('current_role', DEFAULT_ROLE)
            system_prompt_to_use = BOT_ROLES.get(selected_role, BOT_ROLES[DEFAULT_ROLE]) # Fallback just in case
            logger.debug(f"{log_prefix} Using role '{selected_role}' for user {user_id}.")

            messages_payload = [{"role": "system", "content": system_prompt_to_use}]
            messages_payload.extend(conversation_history[user_id])
            request_body = {"model": OLLAMA_MODEL_NAME, "messages": messages_payload, "stream": True}

            # The try_ollama_request function will handle the final endpoint URL construction
            # logger.debug(f"{log_prefix} API Request Payload (for /api/chat): {json.dumps(request_body, indent=2)}") # Can be verbose

            # --- Make the API call --- 
            logger.info(f"{log_prefix} Calling try_ollama_request.")
            success, ai_response = await try_ollama_request(message, user_id, request_body, log_prefix) # Pass prefix

            # --- Handle API Response --- 
            if success and ai_response:
                logger.info(f"{log_prefix} API call successful for user {user_id}.")
                # Add assistant response to chat history since we are using the chat format
                conversation_history[user_id].append({"role": "assistant", "content": ai_response})
                logger.debug(f"{log_prefix} Added assistant response to chat history.")

                # Limit response to two sentences if possible
                first_period_index = ai_response.find('.')
                if first_period_index != -1:
                    second_period_index = ai_response.find('.', first_period_index + 1)
                    if second_period_index != -1:
                        ai_response = ai_response[:second_period_index + 1]
                # If less than two periods, keep the original response

                # --- Send Response to Discord (GIF or Text) --- 
                # Completely disable GIF sending
                gif_sent_successfully = False
                # Always send as text only
                logger.info(f"{log_prefix} Sending text response (GIFs disabled).")
                if len(ai_response) > 2000:
                    for i in range(0, len(ai_response), 2000):
                        await message.reply(ai_response[i:i+2000])
                else:
                    await message.reply(ai_response)
                logger.info(f"{log_prefix} Finished processing successfully.")
                return 
            
            elif not success:
                logger.error(f"{log_prefix} API call failed (success=False). Sending error message.")
                await message.channel.send("⚠️ Sorry, I couldn't get a response from the AI. Please try again later.")
                return
            else: # success True, ai_response empty
                 logger.error(f"{log_prefix} API call succeeded but response was empty. Sending error message.")
                 await message.channel.send("⚠️ Sorry, the AI returned an empty response. Please try again.")
                 return

        except Exception as e:
            logger.error(f"{log_prefix} Unexpected error in on_message processing: {e}", exc_info=True)
            await message.channel.send("⚠️ An unexpected error occurred while processing your message.")
            return

async def try_ollama_request(message, user_id, request_body, log_prefix):
    """
    Attempt to make a request to the Ollama API with the given request body.
    Handles endpoint determination, request sending, stream parsing, and response cleaning.
    Returns a tuple: (bool: success, str|None: response_text)
    """
    api_endpoint = "UNKNOWN"
    try:
        # Determine the correct API endpoint
        # Always use /api/chat for system prompts and history
        base_url = OLLAMA_API_URL
        # Ensure base_url doesn't have a path before joining
        parsed_url = urlparse(base_url)
        base_url_no_path = f"{parsed_url.scheme}://{parsed_url.netloc}"
        api_endpoint = urljoin(base_url_no_path, '/api/chat')
        logger.info(f"{log_prefix} Determined API endpoint for chat: {api_endpoint}")

        logger.debug(f"{log_prefix} API Request Payload: {json.dumps(request_body, indent=2)}") # Log the full payload

        response = requests.post(
            api_endpoint,
            json=request_body,
            stream=True,
            timeout=120
        )

        logger.info(f"{log_prefix} Ollama API Response Status Code: {response.status_code}")

        if response.status_code != 200:
            logger.error(f"{log_prefix} Ollama API error: status {response.status_code}, body: {response.text}")
            return False, None

        full_reply = ""
        received_data = False

        logger.debug(f"{log_prefix} Iterating through response lines...")
        line_count = 0
        for line in response.iter_lines():
            line_count += 1
            # logger.debug(f"{log_prefix} Received line #{line_count} (raw bytes): {line}") # Too verbose
            if line:
                raw_data = "DECODE_ERROR"
                try:
                    raw_data = line.decode("utf-8")
                    # logger.debug(f"{log_prefix} Raw data line #{line_count} from Ollama: {raw_data}") # Too verbose
                    
                    if not raw_data.strip() or raw_data == "data: " or raw_data == ":":
                        # logger.debug(f"{log_prefix} Skipping empty or keep-alive line #{line_count}")
                        continue

                    if raw_data.startswith("data: "):
                        data = raw_data[6:]
                    else:
                        data = raw_data
                        
                    try:
                        json_data = json.loads(data)
                        # logger.debug(f"{log_prefix} Parsed JSON from line #{line_count}: {json_data}") # Too verbose
                    except json.JSONDecodeError as je:
                        logger.warning(f"{log_prefix} JSON parse error on line #{line_count}: {je} - Raw data fragment: {data}")
                        continue 

                    token = ""
                    if "response" in json_data: # /api/generate format
                        token = json_data.get("response", "")
                    elif "message" in json_data and isinstance(json_data["message"], dict): # /api/chat format
                        token = json_data["message"].get("content", "")
                    # else:
                        # logger.debug(f"{log_prefix} No known token key found in JSON line #{line_count}")

                    if token:
                        received_data = True
                        full_reply += token

                    if json_data.get("done", False):
                        logger.info(f"{log_prefix} Ollama stream indicates 'done'. Breaking loop.")
                        break
                        
                except Exception as e:
                    logger.error(f"{log_prefix} Error processing stream line #{line_count}: {e}\nRaw data attempt: {raw_data}\n{traceback.format_exc()}")
                    continue
            # else:
                # logger.debug(f"{log_prefix} Received empty line #{line_count}")
        
        logger.info(f"{log_prefix} Finished iterating through {line_count} lines from Ollama.")

        if not received_data:
            logger.error(f"{log_prefix} No valid tokens extracted from Ollama API stream.")
            return False, None 
        else:
            clean_reply = full_reply.strip()
            clean_reply = re.sub(r'^(User|Assistant):\s*', '', clean_reply, flags=re.MULTILINE)
            clean_reply = clean_reply.strip()

            if not clean_reply:
                 logger.error(f"{log_prefix} Aggregated reply was empty after cleaning.")
                 return False, None

            logger.info(f"{log_prefix} Successfully processed response.")
            return True, clean_reply

    except requests.exceptions.Timeout:
        logger.error(f"{log_prefix} Request to Ollama timed out. Endpoint: {api_endpoint}")
        return False, None
    except requests.exceptions.RequestException as req_err:
        logger.error(f"{log_prefix} Request connection error to Ollama: {req_err}. Endpoint: {api_endpoint}")
        return False, None
    except Exception as e:
        logger.error(f"{log_prefix} Unexpected error in try_ollama_request: {e}\nEndpoint: {api_endpoint}\n{traceback.format_exc()}")
        return False, None

client.run(DISCORD_BOT_TOKEN)
