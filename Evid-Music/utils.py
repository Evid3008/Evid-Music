import aiohttp
import aiofiles
import base64
import gc
import io
import httpx
from io import BytesIO
from .config import bot, logs

def close_all_open_files():
    for obj in gc.get_objects():
        try:
            if isinstance(obj, io.IOBase) and not obj.closed:
                obj.close()
        except Exception:
            continue

def format_seconds(seconds):
    if seconds is not None:
        seconds = int(seconds)
        d, h, m, s = (
            seconds // (3600 * 24),
            seconds // 3600 % 24,
            seconds % 3600 // 60,
            seconds % 3600 % 60,
        )
        if d > 0:
            return "{:02d}:{:02d}:{:02d}:{:02d}".format(d, h, m, s)
        elif h > 0:
            return "{:02d}:{:02d}:{:02d}".format(h, m, s)
        elif m > 0:
            return "{:02d}:{:02d}".format(m, s)
        elif s > 0:
            return "00:{:02d}".format(s)
    return "-"

def format_views(views: int) -> str:
    count = int(views)
    if count >= 1_000_000_000:
        return f"{count / 1_000_000_000:.1f}B"
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    if count >= 1_000:
        return f"{count / 1_000:.1f}K"
    return str(count)

async def fetch_and_save_image(url, save_path):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                async with aiofiles.open(save_path, mode="wb") as file:
                    await file.write(await resp.read())
                return save_path
    return None

async def get_user_logo(user_id):
    try:
        user_chat = await bot.get_chat(user_id)
        return await bot.download_media(user_chat.photo.big_file_id, f"cache/{user_id}.png")
    except Exception:
        user_chat = await bot.get_chat(bot.me.id)
        return await bot.download_media(user_chat.photo.big_file_id, f"cache/{user_id}.png")
    except:
        return BytesIO(base64.b64decode("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百

---

### 4. `Evid-Music/stream.py`
Update the imports to use relative imports.

<xaiArtifact artifact_id="6b890c9f-2bf5-4189-aeb2-c50c74076e1f" artifact_version_id="9e689e86-7146-4936-a48c-9ab297ec853a" title="Evid-Music/stream.py" contentType="text/python">
import httpx
from .config import call, call_config, bot, app, queues, paused, active_audio_chats, active_video_chats, active_media_chats
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .utils import format_seconds, format_views, fetch_and_save_image
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality

async def get_stream_info(query, streamtype):
    api_url = "http://46.250.243.87:1470/youtube"
    api_key = "1a873582a7c83342f961cc0a177b2b26"
    video = True if streamtype.lower() == "video" else False
    params = {"query": query, "video": video, "api_key": api_key}

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(api_url, params=params)
            response.raise_for_status()
            return response.json()
    except Exception:
        return {}

async def is_stream_off(chat_id: int) -> bool:
    mode = paused.get(chat_id)
    if not mode:
        return False
    return mode

async def stream_on(chat_id: int):
    paused[chat_id] = False

async def stream_off(chat_id: int):
    paused[chat_id] = True

async def create_thumbnail(info, user_id):
    # Placeholder for thumbnail creation logic
    # (Original create_thumbnail function was truncated, so not included)
    return info.get("thumbnail")

async def put_queue(chat_id, media_stream, thumbnail, title, duration, stream_type, chat_link, mention):
    queued = queues.get(chat_id, [])
    pos = len(queued) + 1
    queued.append({
        "media_stream": media_stream,
        "thumbnail": thumbnail,
        "title": title,
        "duration": duration,
        "stream_type": stream_type,
        "chat_link": chat_link,
        "mention": mention
    })
    queues[chat_id] = queued
    return pos

async def add_active_audio_chat(chat_id):
    if chat_id not in active_audio_chats:
        active_audio_chats.append(chat_id)

async def add_active_video_chat(chat_id):
    if chat_id not in active_video_chats:
        active_video_chats.append(chat_id)

async def add_active_media_chat(chat_id, stream_type):
    if stream_type.lower() == "audio":
        await add_active_audio_chat(chat_id)
    else:
        await add_active_video_chat(chat_id)
    if chat_id not in active_media_chats:
        active_media_chats.append(chat_id)

async def remove_active_audio_chat(chat_id):
    if chat_id in active_audio_chats:
        active_audio_chats.remove(chat_id)

async def remove_active_video_chat(chat_id):
    if chat_id in active_video_chats:
        active_video_chats.remove(chat_id)

async def remove_active_media_chat(chat_id):
    if chat_id in active_media_chats:
        active_media_chats.remove(chat_id)
    await remove_active_audio_chat(chat_id)
    await remove_active_video_chat(chat_id)

async def log_stream_info(chat_id, title, duration, stream_type, chat_link, mention, thumbnail, pos):
    from .config import LOG_GROUP_ID, bot
    if LOG_GROUP_ID != 0 and chat_id != LOG_GROUP_ID:
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="📡 Join Chat 💬", url=chat_link
                    )
                ],
            ]
        )
        if pos != 0:
            caption = f"""
**➲ Added To Queue At: #{pos}**

**➠ Title:** {title}
**➠ Duration:** {duration}
**➠ Stream Type:** {stream_type}
**➠ Requested By:** {mention}"""
        else:
            caption = f"""
**➲ ✯ 𝐀𝐝𝐚 𝐗 𝐒𝐭𝐫𝐞𝐚𝐦𝐢𝐧𝐠™ ✯  **

**➠ Title:** {title}
**➠ Duration:** {duration}
**➠ Stream Type:** {stream_type}
**➠ Requested By:** {mention}"""
        
        try:
            await bot.send_photo(LOG_GROUP_ID, photo=thumbnail, caption=caption, reply_markup=buttons)
        except Exception:
            pass

async def change_stream(chat_id):
    queued = queues.get(chat_id)
    if queued:
        queued.pop(0)
        
    if not queued:
        await bot.send_message(chat_id, "**😣 Queue is empty, So left\nfrom VC❗...**")
        return await close_stream(chat_id)

    aux = await bot.send_message(
        chat_id, "**👾 Processing...**"
    )
    pos = 0
    media_stream = queued[0].get("media_stream")

    await call.play(chat_id, media_stream, config=call_config)
    
    thumbnail = queued[0].get("thumbnail")
    title = queued[0].get("title")
    duration = queued[0].get("duration")
    stream_type = queued[0].get("stream_type")
    chat_link = queued[0].get("chat_link")
    mention = queued[0].get("mention")
    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="🗑️ Close", callback_data="force_close"
                )
            ],
        ]
    )
    caption = f"""
**➲ ✯ 𝐀𝐝𝐚 𝐗 𝐒𝐭𝐫𝐞𝐚𝐦𝐢𝐧𝐠™ ✯ **

**➠ Title:** {title}
**➠ Duration:** {duration}
**➠ Stream Type:** {stream_type}
**➠ Requested By:** {mention}"""
    try:
        await aux.delete()
    except Exception:
        pass
    await add_active_media_chat(chat_id, stream_type)
    await bot.send_photo(chat_id, photo=thumbnail, caption=caption, has_spoiler=True, reply_markup=buttons)
    await log_stream_info(chat_id, title, duration, stream_type, chat_link, mention, thumbnail, pos)

async def close_stream(chat_id):
    try:
        await call.leave_call(chat_id)
    except Exception:
        pass
    await remove_active_media_chat(chat_id)