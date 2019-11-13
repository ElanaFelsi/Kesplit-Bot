import copy
from pprint import pprint

from telegram.ext import CallbackQueryHandler

from model import DB
from settings import *

db = {}
split_members = []

amount = 0
item = ''


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
        the_text = "Money you're owed:\n"
        for username, amount in owe_dict.items():
            the_text += f"\t🔹 @{username}  {amount}\n"
        context.bot.send_message(chat_id=chat_id, text=the_text)


def split_purchase(context, chat_id, user_id):
    activity_collection = db[chat_id].users_activity
    user_name = list(db[chat_id].users_info.find({'user_id': user_id}))[0]['username']
    debt = round(float(amount) / activity_collection.count(), 1)
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


def split_specific_purchase(update, context, chat_id, from_id):
    global split_members
    from_user_name = list(db[chat_id].users_info.find({'user_id': from_id}))[0]['username']
    activity_collection = db[chat_id].users_activity
    debt = round(float(amount) / (len(split_members)+1), 1)
    for member in split_members:
        user_id = list(db[chat_id].users_info.find({'username': member}))[0]['user_id']
        activity = list(activity_collection.find({'user_id': user_id}))[0]
        activity_dict = copy.deepcopy(activity)
        activity_dict['purchases'].append(item)
        if activity['user_id'] != from_id:
            if from_user_name in activity_dict['debts']:
                activity_dict['debts'][from_user_name] += debt
            else:
                activity_dict['debts'][from_user_name] = debt
        activity_collection.replace_one({'user_id': activity['user_id']}, activity_dict, upsert=True)
    context.bot.send_message(chat_id=chat_id, text=f"🛒 {amount}$ was split by the members you asked.")


def pay(context, chat_id, user_id, amount, member):
    activity_collection = db[chat_id].users_activity
    member = member.replace('@', '')
    amount = float(amount)
    activity_dict = list(activity_collection.find({'user_id': user_id}))[0]
    if member in activity_dict['debts']:

        if activity_dict['debts'][member] - amount == 0:
            activity_dict['debts'].pop(member, None)
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
        try:
            if text == '$':
                db[chat_id].insert_user_info(user_id, username)
                context.bot.send_message(chat_id=chat_id,
                                         text=f"Welcome to ke$plit {update.message.from_user.first_name}🤗!")
            elif text.startswith("$split"):
                lst = text.split()
                if len(lst) < 3: raise AttributeError
                global amount
                amount = lst[1]
                global item
                item = " ".join(lst[2:len(lst)])
                members_inline_keyboard(update, context, chat_id, user_id)
                # split_purchase(context, chat_id, user_id, lst[1], " ".join(lst[2:len(lst)]))
            elif text.startswith("$pay"):
                lst = text.split()
                if len(lst) < 3: raise AttributeError
                amount = lst[1]
                member = " ".join(lst[2:len(lst)])
                pay(context, chat_id, user_id, amount, member)
        except ValueError:
            context.bot.send_message(chat_id=chat_id,
                                     text=f"The money input is incorrect 😬, try again.")
        except AttributeError:
            context.bot.send_message(chat_id=chat_id,
                                     text=f"Incorrect command 😬, hit /help for more info.")


def show_debts(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("I owe others", callback_data='owe others'),
                 InlineKeyboardButton("Others owe me", callback_data='owe me')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose:', reply_markup=reply_markup)


def members_inline_keyboard(update: Update, context: CallbackContext, chat_id, user_id):
    member_keyboard = []
    member_keyboard.append([InlineKeyboardButton('All Members', callback_data='all members')])
    all_users = list(db[chat_id].users_info.find({}))
    for user in all_users:
        if user['user_id'] != user_id:
            username = user['username']
            member_keyboard.append([InlineKeyboardButton('@' + username, callback_data=username)])
    member_keyboard.append([InlineKeyboardButton('Done', callback_data='done'),
                            InlineKeyboardButton('Cancel', callback_data='cancel')])
    reply_markup = InlineKeyboardMarkup(member_keyboard)
    message = update.message.reply_text('Split with:', reply_markup=reply_markup)
    context.user_data["user_message_id"] = message.message_id


def callback_handler(update: Update, context: CallbackContext):
    global split_members
    chat_id = update.effective_chat.id
    query = update.callback_query
    user_id = query.message.reply_to_message.from_user.id

    if query.data == 'owe others':
        owe_others(context, chat_id, user_id)
    elif query.data == 'owe me':
        others_owe_me(context, chat_id, user_id)

    if query.data == 'all members':
        split_purchase(context, chat_id, user_id)

    if query.data == 'done':
        split_specific_purchase(update, context, chat_id, user_id)
        split_members = []
    all_users = list(db[chat_id].users_info.find({}))
    for user in all_users:
        if query.data == user['username'] and user_id != user['user_id']:
            split_members.append(user['username'])

    # member_keyboard = []
    # member_keyboard.append([InlineKeyboardButton('❌' + 'All Members', callback_data='all members')])
    # for user in all_users:
    #   sign_check = '✔' if user['username'] == query.data else '❌'
    #   username = user['username']
    #    member_keyboard.append([InlineKeyboardButton(f'{sign_check}' + '@' + username, callback_data=username)])

    # member_keyboard.append([InlineKeyboardButton('Done', callback_data='done'),
    #                        InlineKeyboardButton('Cancel', callback_data='cancel')])
    # reply_markup = InlineKeyboardMarkup(member_keyboard)
    # context.bot.edit_message_reply_markup(chat_id=chat_id, message_id=context.user_data["user_message_id"],
    #                                          reply_markup=reply_markup)

    # query.edit_message_text(text="✔")
    # context.bot.edit_message_reply_markup(chat_id= chat_id, message_id=update.message.message_id, reply_markup=)
    # split_members.append(user['username'])


def owe_others(context, chat_id, user_id):
    owe_text = f"Money you owe:\n"
    owes_dict = list(db[chat_id].users_activity.find({'user_id': user_id}))[0]['debts']
    if not owes_dict:
        context.bot.send_message(chat_id=chat_id, text="You do not owe anyone money")
    else:
        for user in owes_dict:
            owe_text += f"\t🔹 @{user} {owes_dict[user]}\n"
        context.bot.send_message(chat_id=chat_id, text=owe_text)


def get_help(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    f_name = update.message.from_user.first_name

    context.bot.send_message(chat_id=chat_id, text=f"Don't worry I'm here for the rescue 💪💪\n"
                                                   f"Commands:\n"
                                                   f"/schedule - schedule a paying reminder time\n"
                                                   f"/debts - display your debts\n"
                                                   f"/list - display your last purchases\n"
                                                   f"$ - join ke$plit\n"
                                                   f"$split (amount) (item) - split your purchase with members\n"
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
debts_handler = CommandHandler('debts', show_debts)

updater.dispatcher.add_handler(CallbackQueryHandler(callback_handler, pass_chat_data=True))
dispatcher.add_handler(start_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(schedule_handler)
dispatcher.add_handler(debts_handler)

updater.dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, added_to_group))

echo_handler = MessageHandler(Filters.text, respond)
dispatcher.add_handler(echo_handler)
logger.info("* Start polling...")
updater.start_polling()  # Starts polling in a background thread.
updater.idle()  # Wait until Ctrl+C is pressed
logger.info("* Bye!")
