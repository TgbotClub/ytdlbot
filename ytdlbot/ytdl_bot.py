import asyncio
import logging
import typing
import os
from client_init import create_app
from utils import customize_logger
from pyrogram import Client, filters, types
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import (AUTHORIZED_USER,OWNER)
from pyrogram import errors

# Chose the idiotic way #

DELAY_BETWEEN_EDITS = "2"
PROCESS_RUNNING = "thinking ..."
aktifperintah ={}
inikerjasaatdirektori = os.path.abspath(".")


def hash_msg(message):
    return str(message.chat.id) + "/" + str(message.message_id)

async def read_stream(func, stream, delay):
    last_task = None
    data = b""
    while True:
        dat = (await stream.read(1))
        if not dat:
            # EOF
            if last_task:
                # Send all pending data
                last_task.cancel()
                await func(data.decode("UTF-8"))
                # If there is no last task there is inherently no data, so theres no point sending a blank string
            break
        data += dat
        if last_task:
            last_task.cancel()
        last_task = asyncio.ensure_future(sleep_for_task(func, data, delay))

class MessageEditor():
    def __init__(self, message, command):
        self.message = message
        self.command = command
        self.stdout = ""
        self.stdin = ""
        self.stderr = ""
        self.rc = None
        self.redraws = 0
        self.process = None
        self.state = 0

    async def update_stdout(self, stdout):
        self.stdout = stdout
        await self.redraw()

    async def update_stderr(self, stderr):
        self.stderr = stderr
        await self.redraw()

    async def update_stdin(self, stdin):
        self.stdin = stdin
        await self.redraw()

    async def redraw(self, skip_wait=False):
        text = "<b>Running command</b>: <code>{}<code>".format(self.command) + "\n"
        if self.rc is not None:
            text += "<b>process exited</b> with code <code>{}</code>".format(str(self.rc))
        if len(self.stdout) > 0:
            text += "\n\n" + "<b>STDOUT</b>:" + "\n"
            text += "<code>" + self.stdout[max(len(self.stdout) - 2048, 0):] + "</code>"
        if len(self.stderr) > 0:
            text += "\n\n" + "<b>STDERR</n>:" + "\n"
            text += "<code>" + self.stderr[max(len(self.stderr) - 1024, 0):] + "</code>"
        if len(self.stdin) > 0:
            text += "\n\n" + "<b>STDiN</n>:" + "\n"
            text += "<code>" + self.stdin[max(len(self.stdin) - 1024, 0):] + "</code>"
        try:
            await self.message.edit(text)
        except errors.MessageNotModified:
            pass
        except errors.MessageTooLong as e:
            LOGGER.error(e)
            LOGGER.error(text)
        # The message is never empty due to the template header

    async def cmd_ended(self, rc):
        self.rc = rc
        self.state = 4
        await self.redraw(True)

    def update_process(self, process):
        LOGGER.debug("got sproc obj %s", process)
        self.process = process

# extra imports ended #




customize_logger(["pyrogram.client", "pyrogram.session.session", "pyrogram.connection.connection"])
app = create_app()

logging.info("trying to open Pre-MainFile ...")


@app.on_message(filters.command(["load"]))
def load_handler(client: "Client", message: "types.Message"):
    chat_id = message.chat.id
    client.send_chat_action(chat_id, "typing")
    client.send_message(chat_id, "trying to start bot ...")
    import ytdlbot

# exec commands #

@app.on_message(filters.command(["exec"])
if message.chat.username == OWNER:
 async def execution_cmd_t(client, message):
    # send a message, use it to update the progress when required
    status_message = await message.reply_text(PROCESS_RUNNING, quote=True)
    # get the message from the triggered command
    cmd = message.text.split(" ", maxsplit=1)[1]

    process = await asyncio.create_subprocess_shell(
        cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=inikerjasaatdirektori
    )

    editor = MessageEditor(status_message, cmd)
    editor.update_process(process)

    aktifperintah[hash_msg(status_message)] = editor
    await editor.redraw(True)
    await asyncio.gather(
        read_stream(
            editor.update_stdout,
            process.stdout,
            DELAY_BETWEEN_EDITS
        ),
        read_stream(
            editor.update_stderr,
            process.stderr,
            DELAY_BETWEEN_EDITS
        )
    )
    await editor.cmd_ended(await process.wait())
    del aktifperintah[hash_msg(status_message)]
else:
 client.send_message(chat_id, "idiots can do anything ...")

# exec command ended #

