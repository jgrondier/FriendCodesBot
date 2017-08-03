__author__ = "jgrondier"
__copyright__ = "Copyright 2017"

from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext.dispatcher import run_async
import json, os, configparser
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler
import logging
from uuid import uuid4
import re

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)

code_folder_name = "codes"

dir_path = os.path.dirname(os.path.realpath(__file__))

n3ds_pattern = re.compile("^[0-9]{4}-[0-9]{4}-[0-9]{4}$")

wiiu_pattern = re.compile("[a-zA-Z0-9][\w-]{4,14}[a-zA-Z0-9]")

switch_pattern = re.compile("^SW-[0-9]{4}-[0-9]{4}-[0-9]{4}$")

conf = configparser.ConfigParser()
conf.read("config")

token = conf['DEFAULT']['TOKEN']


def default_dict():
    return {'3DS': None, 'WiiU': None, 'Switch': None}


def read_or_new_json(path, d):
    if os.path.isfile(path):
        with open(path) as infile:
            try:
                return json.load(infile)
            except Exception:  # so many things could go wrong, can't be more specific.
                pass
    else:
        with open(path, "w+") as f:
            json.dump(d, f)
    return d


def get_file_path(update, inline=False):
    if inline:
        sender_id = str(update.inline_query.from_user.id)
    else:
        sender_id = str(update.message.from_user.id)
    return os.path.join(code_folder_name, sender_id)


@run_async
def inlinequery(bot, update):
    file_path = get_file_path(update, inline=True)

    p = read_or_new_json(file_path, default_dict())

    results = [
        InlineQueryResultArticle(id=uuid4(), title=k,
                                 input_message_content=InputTextMessageContent("My {} friend code: {}".format(k, v)),
                                 description=v)
        for k, v in p.items() if v is not None]

    update.inline_query.answer(results, cache_time=0)


def setcode(bot, update, args, type, pattern):
    if len(args) < 1 or not pattern.match(args[0]):
        update.message.reply_text("This doesn't seem to be a valid ID !")
        return

    file_path = get_file_path(update)

    p = read_or_new_json(file_path, default_dict())

    p[type] = args[0]

    with open(file_path, 'w') as outfile:
        json.dump(p, outfile)

    update.message.reply_text("ID updated.")


def setswitch(bot, update, args):
    setcode(bot, update, args, 'Switch', pattern=switch_pattern)


def set3ds(bot, update, args):
    setcode(bot, update, args, '3DS', pattern=n3ds_pattern)


def setwiiu(bot, update, args):
    setcode(bot, update, args, 'WiiU', pattern=wiiu_pattern)


def main():
    updater = Updater(token)

    dp = updater.dispatcher

    dp.add_handler(InlineQueryHandler(inlinequery))

    dp.add_handler(CommandHandler("setSwitch", setswitch, pass_args=True))
    dp.add_handler(CommandHandler("set3DS", set3ds, pass_args=True))
    dp.add_handler(CommandHandler("setWiiU", setwiiu, pass_args=True))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    if not os.path.exists(code_folder_name):
        os.makedirs(code_folder_name)

    main()
