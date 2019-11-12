from pymongo import MongoClient
from collections import defaultdict


class DB:

    def __init__(self, chat_id, chat_name):
        client = MongoClient()
        chat_id = str(chat_id)
        self.db = client.get_database(chat_id)
        self.users_info = self.db.get_collection("users_info")
        self.users_activity = self.db.get_collection("users_activity")

    def insert_user_info(self, user_id, username):
        user = {
            'user_id': user_id,
            'username': username
        }
        self.users_info.replace_one({'user_id':user_id}, user, upsert=True)
        self.init_users_activity(user_id)

    def init_users_activity(self, user_id):
        activity = {
            'user_id': user_id,
            'purchases': [],
            'debts': {}
        }
        self.users_activity.replace_one({'user_id':user_id}, activity, upsert=True)