import time
import asyncio
from .config import bot, app, START_IMAGE_URL, only_owner, clinks, call, call_config, queues
from .database import add_served_user, add_served_chat
from .stream import get_stream_info, create_thumbnail, put_queue, add_active_media_chat, is_stream_off, stream_on, stream_off, change_stream, close_stream
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality
from pyrogram.errors import ChatAdminRequired, UserNotParticipant, InviteRequestSent
from pytgcalls.exceptions import NoActiveGroupCall
from .utils import close_all_open_files, format_seconds

# Store the start time of each song for progress tracking
song_start_times = {}

def chat_admins_only(mystic):
    async def wrapper(client, message):
        if message.sender_chat:
            if message.sender_chat.id != message.chat.id:
                return
                
        if message.from_user:
            if message.from_user.id != OWNER_ID:
                try:
                    member = await bot.get_chat_member(
                        message.chat.id, message.from_user.id
                    )
                except Exception:
                    return
                if not member:
                    return
                try:
                    if not member.privileges.can_manage_video_chats:
                        return
                except Exception:
                    return
        try:
            await message.delete()
        except Exception:
            pass
            
        return await mystic(client, message)

    return wrapper

async def update_progress_bar(chat_id, message_id, duration_seconds):
    """Update the progress bar for the currently playing song."""
    start_time = song_start_times.get(chat_id)
    if not start_time:
        return

    while True:
        elapsed_time = int(time.time() - start_time)
        if elapsed_time >= duration_seconds:
            break

        # Format the progress bar
        current_time = format_seconds(elapsed_time)
        total_time = format_seconds(duration_seconds)
        progress = f"{current_time} / {total_time}"

        # Update the message with the new progress bar
        try:
            message = await bot.get_messages(chat_id, message_id)
            caption = message.caption
            # Replace the progress bar line in the caption
            new_caption = "\n".join(
                line if not line.startswith("**➠ Progress:**") else f"**➠ Progress:** `{progress}`"
                for line in caption.split("\n")
            )
            await bot.edit_message_caption(
                chat_id=chat_id,
                message_id=message_id,
                caption=new_caption,
                reply_markup=message.reply_markup
            )
        except Exception:
            break

        await asyncio.sleep(5)  # Update every 5 seconds

@bot.on_message(filters.command("start") & filters.private)
async def start_welcome_private(client, message):
    chat_id = message.chat.id
    await add_served_user(chat_id)
    photo = START_IMAGE_URL
    mention = message.from_user.mention
    caption = f"""**➲ Hello, {mention}

➲ I'm an advanced Bot, My Owner Mr Evid.

➲ Latest & verƴ powerƒul vc music player bot.

➲ ƒeel ƒree to use me in your chat
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
                    text="⚙️ Open All Commands ⚙️", callback_data="help_menu"
                )
            ],
        ]
    )
    try:
        return await client.send_photo(
        chat_id, photo=photo, caption=caption, has_spoiler=True, reply_markup=buttons
        )
    except Exception:
        pass

@bot.on_message(filters.command("help") & filters.private)
async def open_help_menu_private(client, message):
    chat_id = message.chat.id
    photo = START_IMAGE_URL
    caption = f"""**👀 These are The Commands and
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
        await bot.send_photo(
            chat_id, photo=photo, caption=caption, has_spoiler=True, reply_markup=buttons
        )
    except Exception:
        pass

@bot.on_message(filters.command(["play", "vplay"]) & ~filters.private)
async def start_audio_stream(client, message):
    try:
        await message.delete()
    except Exception:
        pass
    chat_id = message.chat.id
    if message.chat.username:
        chat_link = f"https://t.me/{message.chat.username}"
    else:
        chatlinks = clinks.get(chat_id)
        
        if chatlinks:
            if chatlinks == f"https://t.me/{client.me.username}":
                try:
                    chat_link = await client.export_chat_invite_link(chat_id)
                except Exception:
                    chat_link = chatlinks
            else:
                chat_link = chatlinks
        else:
            try:
                chat_link = await client.export_chat_invite_link(chat_id)
            except Exception:
                chat_link = f"https://t.me/{client.me.username}"
            
    clinks[chat_id] = chat_link
    
    try:
        mention = message.from_user.mention
    except:
        mention = client.me.mention
        
    try:
        user_id = message.from_user.id
    except Exception:
        user_id = client.me.id
        
    try:
        if len(message.command) < 2:
            return await client.send_message(
                chat_id, f"""
**🥀 Give Me Some Query To
Stream Audio Or Video❗...

ℹ️ Example:
≽ Audio: `/play yalgaar`
≽ Video: `/vplay yalgaar`**"""
            )
        aux = await client.send_message(chat_id, "**👾 Processing...**")
        query = message.text.split(None, 1)[1]
        streamtype = "Audio" if not message.command[0].startswith("v") else "Video"
        info = await get_stream_info(query, streamtype)
        if not info:
            return await aux.edit("**😣 Failed to fecth details, try\nanother song.**")
            
        link = info.get("link")
        title = f"[{info.get('title')[:18]}]({link})"
        duration = f"""{
            format_seconds(info.get('duration')) + ' Mins'
            if info.get('duration') else 'Live Stream'
        }"""
        duration_seconds = info.get('duration', 0)  # Get duration in seconds for progress bar
        views = format_views(info.get("views"))
        image = info.get("thumbnail")
        stream_url = info.get("stream_url")
        stream_type = info.get("stream_type")
        
        media_stream = MediaStream(
            media_path=stream_url,
            video_flags=MediaStream.Flags.IGNORE,
            audio_parameters=AudioQuality.STUDIO,
        ) if stream_type != "Video" else MediaStream(
            media_path=stream_url,
            audio_parameters=AudioQuality.STUDIO,
            video_parameters=VideoQuality.HD_720p,
        )
        
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="▶️ Play", callback_data=f"play_{chat_id}"),
                    InlineKeyboardButton(text="⏸️ Pause", callback_data=f"pause_{chat_id}"),
                    InlineKeyboardButton(text="🔄 Replay", callback_data=f"replay_{chat_id}"),
                    InlineKeyboardButton(text="⏭️ Next", callback_data=f"next_{chat_id}"),
                    InlineKeyboardButton(text="⏹️ End", callback_data=f"end_{chat_id}"),
                ],
                [
                    InlineKeyboardButton(text="👤 Owner", url="https://t.me/evidzone"),
                    InlineKeyboardButton(text="💬 Support", url="https://t.me/evidclue"),
                ],
                [
                    InlineKeyboardButton(text="❌ Close", callback_data="force_close"),
                ],
            ]
        )
        
        queued = queues.get(chat_id)
        if queued:
            thumbnail = await create_thumbnail(info, user_id)
            pos = await put_queue(
                chat_id, media_stream, thumbnail, title, duration, stream_type, chat_link, mention
            )
            caption = f"""
**➲ Added To Queue At: #{pos}**

**➠ Title:** {title}
**➠ Duration:** {duration}
**➠ Stream Type:** {stream_type}
**➠ Requested By:** {mention}
**➠ Progress:** `00:00 / {format_seconds(duration_seconds)}`"""
        
        else:
            try: 
                await call.play(chat_id, media_stream, config=call_config)
            except NoActiveGroupCall:
                try:
                    assistant = await client.get_chat_member(chat_id, app.me.id)
                    if (
                        assistant.status == ChatMemberStatus.BANNED
                        or assistant.status == ChatMemberStatus.RESTRICTED
                    ):
                        return await aux.edit_text(
                            f"**🤖 At first, unban [Assistant ID](https://t.me/{app.me.username}) to start stream❗**"
                        )
                except ChatAdminRequired:
                    return await aux.edit_text(
                        "**🤖 At first, Promote me as an admin❗**"
                    )
                except UserNotParticipant:
                    if message.chat.username:
                        invitelink = f"https://t.me/{message.chat.username}"
                        try:
                            await app.resolve_peer(invitelink)
                        except Exception:
                            pass
                    else:
                        try:
                            invitelink = await client.export_chat_invite_link(chat_id)
                        except ChatAdminRequired:
                            return await aux.edit_text(
                                "**🤖 Hey, I need invite user permission to add Assistant ID❗**"
                            )
                        except Exception as e:
                            return await aux.edit_text(
                                f"**🚫 Assistant Error:** `{e}`"
                            )
                    clinks[chat_id] = invitelink
                    try:
                        await asyncio.sleep(1)
                        await app.join_chat(invitelink)
                    except InviteRequestSent:
                        try:
                            await client.approve_chat_join_request(chat_id, app.me.id)
                        except Exception as e:
                            return await aux.edit_text(
                                f"**🚫 Approve Error:** `{e}`"
                            )
                    except UserAlreadyParticipant:
                        pass
                    except Exception as e:
                        return await aux.edit_text(
                            f"**🚫 Assistant Join Error:** `{e}`"
                        )
                try:
                    await call.play(chat_id, media_stream, config=call_config)
                except NoActiveGroupCall:
                    return await aux.edit_text(f"**🤔 No Active VC❗...**")
            except TelegramServerError:
                return await aux.edit_text("**🤔 Telegram Server Issue❗...**")
                
            thumbnail = await create_thumbnail(info, user_id)
            pos = await put_queue(
                chat_id, media_stream, thumbnail, title, duration, stream_type, chat_link, mention
            )
            caption = f"""
**➲ ✯ 𝐀𝐝𝐚 𝐗 𝐒𝐭𝐫𝐞𝐚𝐦𝐢𝐧𝐠™ ✯  ✯**

**➠ Title:** {title}
**➠ Duration:** {duration}
**➠ Stream Type:** {stream_type}
**➠ Requested By:** {mention}
**➠ Progress:** `00:00 / {format_seconds(duration_seconds)}`"""
        
        try:
            await aux.delete()
        except Exception:
            pass
        sent_message = await client.send_photo(chat_id, photo=thumbnail, caption=caption, has_spoiler=True, reply_markup=buttons)
        await add_active_media_chat(chat_id, stream_type)
        await add_served_chat(chat_id)
        await log_stream_info(chat_id, title, duration, stream_type, chat_link, mention, thumbnail, pos)

        # Store the start time and start the progress bar update task
        if pos == 0:  # Only for the currently playing song
            song_start_times[chat_id] = time.time()
            asyncio.create_task(update_progress_bar(chat_id, sent_message.id, duration_seconds))
    except Exception as e:
        if "too many open files" in str(e).lower():
            close_all_open_files()
        logs.error(str(e))
        await aux.edit("**😣 Failed to stream❗...**")

@bot.on_message(filters.command("pause") & ~filters.private)
@chat_admins_only
async def pause_current_stream(client, message):
    chat_id = message.chat.id
    queued = queues.get(chat_id)
    if not queued:
        return await message.reply_text(
            "**🤔 Nothing Streaming.**"
        )
    is_stream = await is_stream_off(chat_id)
    if is_stream:
        return await message.reply_text(
            "**😏 Stream already Paused.**"
        )
    try:
        await call.pause(chat_id)
    except Exception:
        return await message.reply_text(
            "**❌ Failed to pause stream❗**"
        )
    await stream_off(chat_id)
    return await message.reply_text("**👀 Stream now Paused.**")

@bot.on_message(filters.command("resume") & ~filters.private)
@chat_admins_only
async def resume_current_stream(client, message):
    chat_id = message.chat.id
    queued = queues.get(chat_id)
    if not queued:
        return await message.reply_text(
            "**😣 Nothing Streaming.**"
        )
    is_stream = await is_stream_off(chat_id)
    if not is_stream:
        return await message.reply_text(
            "**👀 Stream already Running.**"
        )
    try:
        await call.resume(chat_id)
    except Exception:
        return await message.reply_text(
            "**❌ Failed to resume stream❗**"
        )
    await stream_on(chat_id)
    return await message.reply_text("**✅ Stream now Resumed.**")

@bot.on_message(filters.command("end") & ~filters.private)
@chat_admins_only
async def stop_running_stream(client, message):
    chat_id = message.chat.id
    queued = queues.get(chat_id)
    if not queued:
        return await message.reply_text(
            "**❌ Nothing Streaming.**"
        )
    await close_stream(chat_id)
    return await message.reply_text("**❎ Streaming Stopped.**")

@bot.on_message(filters.command("skip") & ~filters.private)
@chat_admins_only
async def skip_current_stream(client, message):
    chat_id = message.chat.id
    queued = queues.get(chat_id)
    if not queued:
        return await message.reply_text(
            "**❌ Nothing streaming❗**"
        )
    return await change_stream(chat_id)

@bot.on_message(filters.command("stats") & only_owner)
async def check_stats(client, message):
    from .database import get_served_chats, get_served_users
    try:
        await message.delete()
    except Exception:
        pass
    active_audio = len(active_audio_chats)
    active_video = len(active_video_chats)
    total_chats = len(await get_served_chats())
    total_users = len(await get_served_users())
    
    caption = f"""
**✅ Active Audio Chats:** `{active_audio}`
**✅ Active Video Chats:** `{active_video}`

**✅ Total Served Chats:** `{total_chats}`
**✅ Total Served Users:** `{total_users}`
"""
    return await message.reply_text(caption)

@bot.on_message(filters.command(["broadcast", "gcast"]) & only_owner)
async def broadcast_message(client, message):
    from .database import get_served_chats, get_served_users
    try:
        await message.delete()
    except:
        pass
    if message.reply_to_message:
        x = message.reply_to_message.id
        y = message.chat.id
    else:
        if len(message.command) < 2:
            return await message.reply_text(
                f"""**🤖 Hey Give Me Some Text
Or Reply To A Message❗**"""
            )
        query = message.text.split(None, 1)[1]
        if "-pin" in query:
            query = query.replace("-pin", "")
        if "-nobot" in query:
            query = query.replace("-nobot", "")
        if "-pinloud" in query:
            query = query.replace("-pinloud", "")
        if "-user" in query:
            query = query.replace("-user", "")
        if query == "":
            return await message.reply_text(
                f"""**🤖 Hey Give Me Some Text
Or Reply To A Message❗**"""
            )

    # Bot broadcast inside chats
    if "-nobot" not in message.text:
        sent = 0
        pin = 0
        chats = []
        schats = await get_served_chats()
        for chat in schats:
            chats.append(int(chat["chat_id"]))
        for i in chats:
            try:
                m = (
                    await bot.forward_messages(i, y, x)
                    if message.reply_to_message
                    else await bot.send_message(i, text=query)
                )
                if "-pin" in message.text:
                    try:
                        await m.pin(disable_notification=True)
                        pin += 1
                    except Exception:
                        continue
                elif "-pinloud" in message.text:
                    try:
                        await m.pin(disable_notification=False)
                        pin += 1
                    except Exception:
                        continue
                sent += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                continue
            except Exception:
                continue
        await message.reply_text(f"**✅ Global Broadcast Done.**\n\n__🤖 Broadcast Mesaages In\n{sent} Chats With {pin} Pins.__")

    # Bot broadcasting to users
    if "-user" in message.text:
        susr = 0
        served_users = []
        susers = await get_served_users()
        for user in susers:
            served_users.append(int(user["user_id"]))
        for i in served_users:
            try:
                m = (
                    await bot.forward_messages(i, y, x)
                    if message.reply_to_message
                    else await bot.send_message(i, text=query)
                )
                susr += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                continue
            except Exception:
                continue
        await message.reply_text(f"**✅ Global Broadcast Done.**\n\n__🤖 Broascast Mesaages To\n{susr} Users From Bot.__")

@bot.on_message(filters.command("post") & only_owner)
async def post_bot_promotion(client, message):
    from .database import get_served_chats, get_served_users
    total_chats = []
    schats = await get_served_chats()
    for chat in schats:
        total_chats.append(int(chat["chat_id"]))
    susers = await get_served_users()
    for user in susers:
        total_chats.append(int(user["user_id"]))
            
    photo = START_IMAGE_URL
    caption = f"""
**✅ Hello friends,

➠ i am an advanced, latest &
verƴ powerƒul vc player bot.

➠ ƒeel ƒree to use me & share
with your other ƒriends.**"""
    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="➕ Add Me in Your Chat ➕", url=f"https://t.me/{client.me.username}?startgroup=true",
                )
            ]
        ]
    )
    sent = 0
    for chat_id in total_chats:
        try:
            m = await client.send_photo(
                chat_id, photo=photo, caption=caption, reply_markup=buttons
            )
            sent = sent + 1
            await asyncio.sleep(5)
            try:
                await m.pin(disable_notification=False)
            except Exception:
                continue
        except FloodWait as e:
            await asyncio.sleep(e.value)
            continue
        except Exception:
            continue
    return await message.reply_text(f"**✅ Successfully posted in {sent} chats.**")

@bot.on_message(filters.new_chat_members, group=-1)
async def add_chat_id(client, message):
    chat_id = message.chat.id
    for member in message.new_chat_members:
        if member.id == bot.me.id:
            await add_served_chat(chat_id)