from .config import call
from .stream import close_stream, change_stream
from pytgcalls import filters as fl
from pytgcalls.types import ChatUpdate, Update

@call.on_update(fl.chat_update(ChatUpdate.Status.CLOSED_VOICE_CHAT))
@call.on_update(fl.chat_update(ChatUpdate.Status.KICKED))
@call.on_update(fl.chat_update(ChatUpdate.Status.LEFT_GROUP))
async def stream_services_handler(_, update: Update):
    return await close_stream(update.chat_id)

@call.on_update(fl.stream_end())
async def stream_end_handler(_, update: Update):
    chat_id = update.chat_id
    return await change_stream(chat_id)