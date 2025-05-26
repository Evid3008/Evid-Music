import asyncio
import os
import sys
from .config import bot, app, call, adb_cli, LOG_GROUP_ID, logs
from pyrogram import idle

async def main():
    if "cache" not in os.listdir():
        os.mkdir("cache")
    if "downloads" not in os.listdir():
        os.mkdir("downloads")
    for file in os.listdir():
        if file.endswith(".session"):
            os.remove(file)
    for file in os.listdir():
        if file.endswith(".session-journal"):
            os.remove(file)
    try:
        await adb_cli.admin.command('ping')
    except Exception:
        logs.info("⚠️ 'MONGO_DB_URL' - Not Valid !!")
        sys.exit()
        
    try:
        await bot.start()
    except Exception as e:
        logs.info(f"🚫 Failed to start Bot❗\n⚠️ Reason: {e}")
        sys.exit()
    if LOG_GROUP_ID != 0:
        try:
            await bot.send_message(
                LOG_GROUP_ID, "**💖 Bot Started.**"
            )
        except Exception:
            pass
    logs.info("💖 Bot Started❗")
    try:
        await app.start()
    except Exception as e:
        logs.info(f"🚫 Failed to start Assistant❗\n⚠️ Reason: {e}")
        sys.exit()
    try:
        await app.join_chat("evidzone")
        await app.join_chat("evidclue")
    except Exception:
        pass
    if LOG_GROUP_ID != 0:
        try:
            await app.send_message(
                LOG_GROUP_ID, "**💖 Assistant Started.**"
            )
        except Exception:
            pass
    logs.info("💖 Assistant Started❗")
    try:
        await call.start()
    except Exception as e:
        logs.info(f"🚫 Failed to start PyTgCalls❗\n⚠️ Reason: {e}")
        sys.exit()
    await idle()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    logs.info("❎ Goodbye, Bot Has Been Stopped‼️")
