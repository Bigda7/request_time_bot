import os
import asyncio
import logging
import time
import aiohttp
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
API_TOKEN = os.getenv("API_TOKEN")
DB_URL = os.getenv("DB_URL")
YOUR_CHAT_ID = int(os.getenv("YOUR_CHAT_ID", 0))

is_paused = False

# --- DATABASE SETUP ---
Base = declarative_base()
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)


class Website(Base):
    __tablename__ = "websites"
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(engine)

# --- BOT SETUP ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()


def is_admin(message: types.Message) -> bool:
    """Checks if the user is the authorized owner of the bot."""
    return message.from_user.id == YOUR_CHAT_ID


# --- ASYNCHRONOUS MONITORING LOGIC ---


async def check_url(session: aiohttp.ClientSession, url: str):
    """Asynchronous background check for a single website."""
    headers = {"User-Agent": "Mozilla/5.0"}
    url_to_check = url if url.startswith(("http://", "https://")) else "https://" + url

    try:
        # Set a 10-second timeout for the request
        timeout = aiohttp.ClientTimeout(total=10)
        async with session.get(
            url_to_check, headers=headers, timeout=timeout
        ) as response:
            return url, response.status in [200, 401, 403]
    except Exception as e:
        logging.error(f"Error checking {url}: {e}")
        return url, False


async def get_detailed_status(session: aiohttp.ClientSession, url: str):
    """Asynchronous manual status check with response time measurement."""
    headers = {"User-Agent": "Mozilla/5.0"}
    url_to_check = url if url.startswith(("http://", "https://")) else "https://" + url

    start_time = time.monotonic()  # Start the response timer

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with session.get(
            url_to_check, headers=headers, timeout=timeout
        ) as response:
            load_time = round(time.monotonic() - start_time, 2)

            # aiohttp uses response.status, not status_code
            if response.status == 200:
                return f"✅ {url} | {load_time}s"
            elif response.status in [401, 403]:
                return f"🛡️ {url} | {load_time}s (Protected)"
            else:
                return f"⚠️ {url} | Error {response.status}"

    except asyncio.TimeoutError:
        return f"⏳ {url} | Timeout (10s)"
    except aiohttp.ClientError:
        return f"❌ {url} | Connection Failed"


last_known_status = {}


async def background_monitor():
    """Runs infinite loop checking all databases URLs concurrently."""
    global is_paused
    while True:
        if is_paused:
            await asyncio.sleep(60)
            continue

        db_session = Session()
        sites = db_session.query(Website).all()
        db_session.close()

        if sites:
            urls = [s.url for s in sites]

            # Open a single ClientSession for all concurrent requests
            async with aiohttp.ClientSession() as http_session:
                tasks = [check_url(http_session, url) for url in urls]
                # Execute all requests concurrently
                results = await asyncio.gather(*tasks)

            for url, is_online in results:
                was_online = last_known_status.get(url, True)

                if not is_online and was_online:
                    await bot.send_message(YOUR_CHAT_ID, f"🚨 ALERT: {url} is DOWN!")
                    last_known_status[url] = False

                elif is_online and not was_online:
                    await bot.send_message(
                        YOUR_CHAT_ID, f"✅ RECOVERY: {url} is back ONLINE!"
                    )
                    last_known_status[url] = True

        await asyncio.sleep(300)


# --- COMMAND HANDLERS ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if not is_admin(message):
        return await message.answer("Sorry, you are not authorized to use this bot.")

    welcome_text = (
        "Hello! I am your Website Monitoring Bot 🤖\n\n"
        "Commands you can use:\n"
        "/add <url> - Add a new website to monitor\n"
        "/remove <id> - Stop monitoring a website\n"
        "/list - Show database IDs and URLs\n"
        "/status - Run a live check on all websites"
    )
    await message.answer(welcome_text)


@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    if not is_admin(message):
        return
    await message.answer("⏳ Pinging websites asynchronously, please wait...")

    db_session = Session()
    sites = db_session.query(Website).all()
    db_session.close()

    if not sites:
        return await message.answer("Your monitor list is empty. Use /add first.")

    urls = [s.url for s in sites]

    async with aiohttp.ClientSession() as http_session:
        tasks = [get_detailed_status(http_session, url) for url in urls]
        results = await asyncio.gather(*tasks)

    report = "📊 **Live Status Report:**\n\n" + "\n".join(results)
    await message.answer(report, parse_mode="Markdown")


@dp.message(Command("add"))
async def add_site(message: types.Message):
    if not is_admin(message):
        return
    url = message.text.replace("/add ", "").strip()
    if not url:
        return await message.answer("Usage: /add example.com")

    db_session = Session()
    new_site = Website(url=url)
    try:
        db_session.add(new_site)
        db_session.commit()
        await message.answer(f"✅ Added {url} to monitoring.")
    except IntegrityError:
        db_session.rollback()
        await message.answer("❌ This URL is already in the database.")
    finally:
        db_session.close()


@dp.message(Command("remove"))
async def remove_site(message: types.Message):
    if not is_admin(message):
        return
    try:
        site_id = int(message.text.replace("/remove ", "").strip())
        db_session = Session()
        site = db_session.query(Website).filter(Website.id == site_id).first()
        if site:
            url = site.url
            db_session.delete(site)
            db_session.commit()
            await message.answer(f"🗑 Removed {url} from monitoring.")
        else:
            await message.answer("❌ Site with this ID not found.")
        db_session.close()
    except ValueError:
        await message.answer("Usage: /remove <ID>\nExample: /remove 1")


@dp.message(Command("list"))
async def list_sites(message: types.Message):
    if not is_admin(message):
        return
    db_session = Session()
    sites = db_session.query(Website).all()
    db_session.close()

    if not sites:
        return await message.answer("Your monitor list is empty.")
    response = "📋 Monitored Websites:\n" + "\n".join(
        [f"{s.id}. {s.url}" for s in sites]
    )
    await message.answer(response)


@dp.message(Command("pause"))
async def cmd_pause(message: types.Message):
    if not is_admin(message):
        return
    global is_paused
    is_paused = True
    await message.answer(
        "⏸ **Monitoring Paused!**\nSend /resume to start again.", parse_mode="Markdown"
    )


@dp.message(Command("resume"))
async def cmd_resume(message: types.Message):
    if not is_admin(message):
        return
    global is_paused
    is_paused = False
    await message.answer(
        "▶️ **Monitoring Resumed!**\nBackground checks are active again.",
        parse_mode="Markdown",
    )


@dp.message()
async def unknown_message(message: types.Message):
    if not is_admin(message):
        return
    await message.answer(
        "I don't understand this command. Try /start, /status, or /add."
    )


async def set_default_commands(bot: Bot):
    commands = [
        types.BotCommand(command="start", description="Restart bot / Show info"),
        types.BotCommand(command="status", description="Run a live check on all sites"),
        types.BotCommand(command="list", description="Show monitored websites"),
        types.BotCommand(command="add", description="Add a new website"),
        types.BotCommand(command="remove", description="Stop monitoring a website"),
        types.BotCommand(command="pause", description="Pause background alerts"),
        types.BotCommand(command="resume", description="Resume background alerts"),
    ]
    await bot.set_my_commands(commands)


async def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("⏳ Starting the database and background tasks....")

    await set_default_commands(bot)
    asyncio.create_task(background_monitor())

    logging.info("✅ The bot is successfully connected to Telegram and ready!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
