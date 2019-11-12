# YOUR NOT-SECRET SETTINGS HERE
# DON'T PUT YOUR SECRET TOKEN HERE!!!!

import secret_settings
import logging
import telegram
import telepot as telepot
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, \
    Filters, Updater


logger = logging.getLogger(__name__)

updater = Updater(token=secret_settings.BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

logging.basicConfig(
    format='[%(levelname)s %(asctime)s %(module)s:%(lineno)d] %(message)s',
    level=logging.INFO)