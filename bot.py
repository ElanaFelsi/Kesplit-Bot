import copy
from pprint import pprint

from settings import *
from model import DB

db = {}


def build_menu(buttons,
               n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])
    return menu


def added_to_group(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    group_name = update.effective_chat.title
    global db
    db[chat_id] = DB(chat_id, group_name)
    context.bot.send_message(chat_id=chat_id, text=f"Welcome all 😄, I am your money manager! "
                                                   f"If you want to join ke$plit 💰, just say $. \n"
                                                   f"When you need my help hit /help.")



def split_purchase(context, chat_id, user_id, amount, item):
    activity_collection = db[chat_id].users_activity
    user_name = list(db[chat_id].users_info.find({'user_id': user_id}))[0]['username']
    debt = float(amount) / activity_collection.count()
    for activity in activity_collection.find():
        activity_dict = copy.deepcopy(activity)
        activity_dict['purchases'].append(item)
        if activity['user_id'] != user_id:
            if user_name in activity_dict['debts']:
                activity_dict['debts'][user_name] += debt
            else:
                activity_dict['debts'][user_name] = debt
        activity_collection.replace_one({'user_id': activity['user_id']}, activity_dict, upsert=True)
    context.bot.send_message(chat_id=chat_id, text=f"🛒 {amount}$ was split by all members")


def respond(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    text = str(update.message.text)
    if text.startswith("$"):
        if text == '$':
            db[chat_id].insert_user_info(user_id, username)
            context.bot.send_message(chat_id=chat_id,
                                     text=f"Welcome to ke$plit {update.message.from_user.first_name}🤗!")
        elif text.startswith("$split"):
            try:
                lst = text.split()
                split_purchase(context, chat_id, user_id, lst[1], " ".join(lst[2:len(lst)]))
            except ValueError:
                context.bot.send_message(chat_id=chat_id,
                                         text=f"I don't know such money 😬, try again.")


def get_help(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    f_name = update.message.from_user.first_name
    context.bot.send_message(chat_id=chat_id, text=f"Don't worry I'm here for the rescue 💪💪\n"
                                                   f"Commands:\n"
                                                   f"$ - join ke$plit\n"
                                                   f"$split (amount) (item) - split your purchase with all members\n")
    logger.info(f"! {f_name} asked for help!")


start_handler = CommandHandler('start', added_to_group)
help_handler = CommandHandler('help', get_help)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(help_handler)

updater.dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, added_to_group))

echo_handler = MessageHandler(Filters.text, respond)
dispatcher.add_handler(echo_handler)
logger.info("* Start polling...")
updater.start_polling()  # Starts polling in a background thread.
updater.idle()  # Wait until Ctrl+C is pressed
logger.info("* Bye!")
