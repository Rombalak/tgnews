import asyncio
import logging
import json
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telethon.errors.rpcerrorlist import PhoneMigrateError, NetworkMigrateError, UserMigrateError

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота и API данные
BOT_TOKEN = '7674088252:AAGZ2DlHC__IUWokiX-gey4CJLboAu9mEMI'
API_ID = '25168061'
API_HASH = '09c41f487f3f01e2496aed2e831578a2'
GROUP_CHAT_ID = -1002266503774
BOT_CHAT_ID = 7674088252
SESSION_NAME = 'forward_bot'

# Путь к файлу конфигурации
CONFIG_FILE = "config.json"

# Загрузка конфигурации из файла
def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"sources": [], "keywords": [], "full_repost_sources": []}

# Сохранение конфигурации в файл
def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

# Инициализация конфигурации
config = load_config()
sources = config["sources"]
keywords = config["keywords"]
full_repost_sources = config["full_repost_sources"]

# Инициализация Telethon клиента
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

@client.on(events.NewMessage(chats=sources))
async def handler(event):
    try:
        message = event.message.message
        chat = await event.get_chat()
        sender = await event.get_sender()
        logger.info(f"New message from {sender.username} in {chat.title}: {message}")

        # Анализируем сообщение на наличие ключевых слов
        if any(keyword in message for keyword in keywords):
            await client.forward_messages(GROUP_CHAT_ID, event.message)
            logger.info(f"Message forwarded from {sender.username} to group")

        # Если источник в списке для полного репоста, пересылаем сообщение
        if event.chat.username in full_repost_sources:
            await client.forward_messages(GROUP_CHAT_ID, event.message)
            logger.info(f"Message fully reposted from {sender.username} to group")

    except Exception as e:
        logger.error(f"Error processing message from {sender.username}: {e}")

async def main():
    await client.start(bot_token=BOT_TOKEN)

    # Retry logic for Telethon connection
    for attempt in range(1, 6):
        try:
            await client.connect()
            if await client.is_user_authorized():
                logger.info("Telethon client connected and authorized.")
                break
        except (PhoneMigrateError, NetworkMigrateError, UserMigrateError) as e:
            logger.warning(f"Attempt {attempt} at connecting failed: {e}")
            if attempt == 5:
                raise e
            await asyncio.sleep(1)

    logger.info("Bot and Telethon client are running...")

    # Бесконечный цикл для поддержания работы бота
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")