import copy
from pprint import pprint

import telegram.ext

from model import DB
from settings import *

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


def others_owe_me(context, chat_id, user_id):
    owe_dict = {}
    activity_collection = db[chat_id].users_activity
    user_name = list(db[chat_id].users_info.find({'user_id': user_id}))[0]['username']
    for activity in activity_collection.find():
        if activity['user_id'] != user_id:
            if user_name in activity['debts']:
                owe_username = list(db[chat_id].users_info.find({'user_id': activity['user_id']}))[0]['username']
                owe_dict[owe_username] = activity['debts'][user_name]
    if not owe_dict:
        context.bot.send_message(chat_id=chat_id, text="No one owes you money!")
    else:
        the_text = "people that owe you money:\n"
        for username, amount in owe_dict.items():
            the_text += f"\t🔹 @{username}  {round(amount, 2)}\n"
        context.bot.send_message(chat_id=chat_id, text=the_text)


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


def pay(context, chat_id, user_id, amount, member):
    activity_collection = db[chat_id].users_activity
    member = member.replace('@', '')
    amount = float(amount)
    activity_dict = list(activity_collection.find({'user_id': user_id}))[0]
    if member in activity_dict['debts']:

        if activity_dict['debts'][member] - amount == 0:
            activity_dict['debts'][member] -= amount
            context.bot.send_message(chat_id=chat_id, text=f"You payed off all debts to @{member} \n"
                                                           f"Keep it up 🤩")
        elif activity_dict['debts'][member] - amount < 0:
            difference = amount - activity_dict['debts'][member]
            activity_dict['debts'].pop(member, None)
            owes_me_id = list(db[chat_id].users_info.find({'username': member}))[0]['user_id']
            user_name = list(db[chat_id].users_info.find({'user_id': user_id}))[0]['username']
            owes_me_dict = list(activity_collection.find({'user_id': owes_me_id}))[0]
            if user_name in owes_me_dict['debts']:
                owes_me_dict['debts'][user_name] += difference
            else:
                owes_me_dict['debts'][user_name] = difference
                pprint(owes_me_dict)
            activity_collection.replace_one({'user_id': owes_me_id}, owes_me_dict, upsert=True)
            context.bot.send_message(chat_id=chat_id, text=f"You payed @{member} too much,\n"
                                                           f"now @{member} owes you {owes_me_dict['debts'][user_name]} "
                                                           f"🤑")
        else:
            owe = activity_dict['debts'][member] - amount
            activity_dict['debts'][member] -= amount
            context.bot.send_message(chat_id=chat_id, text=f"You you still owe @{member} {owe} 🤢")
    else:
        context.bot.send_message(chat_id=chat_id, text=f"You don't owe @{member} money")
    activity_collection.replace_one({'user_id': activity_dict['user_id']}, activity_dict, upsert=True)


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

        elif text.startswith("$pay"):
            try:
                lst = text.split()
                amount = lst[1]
                member = " ".join(lst[2:len(lst)])
                pay(context, chat_id, user_id, amount, member)
            except ValueError:
                context.bot.send_message(chat_id=chat_id,
                                         text=f"I don't know such money 😬, try again.")

        elif text.startswith("$owe me"):
            others_owe_me(context, chat_id, user_id)

        elif text.startswith("$I owe"):
            owe_others(context, chat_id, user_id)

    #
    # keyboard = [[InlineKeyboardButton("I owe others", callback_data='1'),
    #              InlineKeyboardButton("Others owe me", callback_data='2')]]
    #
    # reply_markup = InlineKeyboardMarkup(keyboard)
    #
    # update.message.reply_text('Please choose:', reply_markup=reply_markup)


def owe_others(context, chat_id, user_id):
    owe_text = f"peoples that you owe them money:\n"
    owes_dict = list(db[chat_id].users_activity.find({'user_id': user_id}))[0]['debts']
    if not owes_dict:
        context.bot.send_message(chat_id=chat_id, text="You do not owe anyone money")
    else:
        for user in owes_dict:
            owe_text += f"\t🔹 {user} {round(owes_dict[user], 2)}\n"
        context.bot.send_message(chat_id=chat_id, text=owe_text)


def get_help(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    f_name = update.message.from_user.first_name

    context.bot.send_message(chat_id=chat_id, text=f"Don't worry I'm here for the rescue 💪💪\n"
                                                   f"Commands:\n"
                                                   f"/schedule - schedule a paying reminder time\n"
                                                   f"/debts - display your debts\n"
                                                   f"$ - join ke$plit\n"
                                                   f"$split (amount) (item) - split your purchase with all members\n"
                                                   f"$pay (amount) (member) - pays member amount you owe him")

    logger.info(f"! {f_name} asked for help!")


def remind(context: telegram.ext.CallbackContext):
    # chat_id = update.effective_chat.id
    context.bot.send_message(chat_id=context.job.context, text=f"🔔Reminder🔔\n"
                                                               f"Hi guys!! Just reminding you all to pay your debts\n")


def schedule_reminder(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id=chat_id, text=f"I'll remind you guys to pay every minute⏰"
                                                   f"I'll start now!\n")
    j = updater.job_queue
    job_minute = j.run_repeating(remind, interval=60, context=update.message.chat_id, first=1)


start_handler = CommandHandler('start', added_to_group)
schedule_handler = CommandHandler('schedule', schedule_reminder)
help_handler = CommandHandler('help', get_help)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(schedule_handler)

updater.dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, added_to_group))

echo_handler = MessageHandler(Filters.text, respond)
dispatcher.add_handler(echo_handler)
logger.info("* Start polling...")
updater.start_polling()  # Starts polling in a background thread.
updater.idle()  # Wait until Ctrl+C is pressed
logger.info("* Bye!")
