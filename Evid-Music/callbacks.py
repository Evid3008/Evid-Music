from .config import bot, call, START_IMAGE_URL, queues
from .stream import stream_on, stream_off, is_stream_off, change_stream, close_stream
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@bot.on_callback_query(filters.regex("help_menu"))
async def open_help_menu_cb(client, query):
    caption = f"""**✅ These are The Commands and
Their Uses.

/play - play music by name.
/vplay - play video by name.
/pause - pause running stream.
/resume - resume paused stream.
/skip - skip to next stream.
/end - stop stream & clear queue.**"""
    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="➕ Add Me in Your Chat ➕", url=f"https://t.me/{client.me.username}?startgroup=true",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Back To Home Menu 🏠", callback_data="home_menu"
                )
            ],
        ]
    )
    try:
        await query.edit_message_caption(caption=caption, reply_markup=buttons)
    except Exception:
        pass

@bot.on_callback_query(filters.regex("home_menu"))
async def open_help_menu_cb(client, query):
    mention = query.from_user.mention
    caption = f"""**✅ Hello, {mention}

➠ i am an advanced, latest & verƴ
powerƒul vc music player bot.

➠ ƒeel ƒree to use me in your chat
& share with your other ƒriends.**"""
    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="➕ Add Me in Your Chat ➕", url=f"https://t.me/{client.me.username}?startgroup=true",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙ Open All Commands ⚙", callback_data="help_menu"
                )
            ],
        ]
    )
    try:
        await query.edit_message_caption(caption=caption, reply_markup=buttons)
    except Exception:
        pass

@bot.on_callback_query(filters.regex("force_close"))
async def force_close_anything(client, query):
    try:
        await query.message.delete()
    except Exception:
        pass

@bot.on_callback_query(filters.regex(r"play_(\d+)"))
async def play_stream_cb(client, query):
    chat_id = int(query.data.split("_")[1])
    queued = queues.get(chat_id)
    if not queued:
        await query.answer("Nothing is streaming!", show_alert=True)
        return
    is_paused = await is_stream_off(chat_id)
    if not is_paused:
        await query.answer("Stream is already playing!", show_alert=True)
        return
    try:
        await call.resume(chat_id)
        await stream_on(chat_id)
        await query.answer("Stream resumed!")
    except Exception as e:
        await query.answer(f"Failed to resume stream: {e}", show_alert=True)

@bot.on_callback_query(filters.regex(r"pause_(\d+)"))
async def pause_stream_cb(client, query):
    chat_id = int(query.data.split("_")[1])
    queued = queues.get(chat_id)
    if not queued:
        await query.answer("Nothing is streaming!", show_alert=True)
        return
    is_paused = await is_stream_off(chat_id)
    if is_paused:
        await query.answer("Stream is already paused!", show_alert=True)
        return
    try:
        await call.pause(chat_id)
        await stream_off(chat_id)
        await query.answer("Stream paused!")
    except Exception as e:
        await query.answer(f"Failed to pause stream: {e}", show_alert=True)

@bot.on_callback_query(filters.regex(r"replay_(\d+)"))
async def replay_stream_cb(client, query):
    chat_id = int(query.data.split("_")[1])
    queued = queues.get(chat_id)
    if not queued:
        await query.answer("Nothing is streaming!", show_alert=True)
        return
    try:
        media_stream = queued[0].get("media_stream")
        await call.play(chat_id, media_stream, config=call_config, force=True)
        await stream_on(chat_id)
        await query.answer("Replaying the current song!")
    except Exception as e:
        await query.answer(f"Failed to replay stream: {e}", show_alert=True)

@bot.on_callback_query(filters.regex(r"next_(\d+)"))
async def next_stream_cb(client, query):
    chat_id = int(query.data.split("_")[1])
    queued = queues.get(chat_id)
    if not queued:
        await query.answer("Nothing is streaming!", show_alert=True)
        return
    try:
        await change_stream(chat_id)
        await query.answer("Skipped to the next song!")
    except Exception as e:
        await query.answer(f"Failed to skip stream: {e}", show_alert=True)

@bot.on_callback_query(filters.regex(r"end_(\d+)"))
async def end_stream_cb(client, query):
    chat_id = int(query.data.split("_")[1])
    queued = queues.get(chat_id)
    if not queued:
        await query.answer("Nothing is streaming!", show_alert=True)
        return
    try:
        await close_stream(chat_id)
        await query.answer("Streaming stopped!")
        await query.message.delete()
    except Exception as e:
        await query.answer(f"Failed to stop stream: {e}", show_alert=True)