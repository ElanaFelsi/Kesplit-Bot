from pymongo import MongoClient


class DB:

    def __init__(self, chat_id, chat_name):
        client = MongoClient()
        self.db = client.get_database(chat_id)
        self.users_info = self.db.get_collection("users_info")
        self.users_activity = self.db.get_collection("users_activity")

    def insert_user_info(self, first_name, last_name, user_id):
        user = {
            'first_name': first_name,
            'last_name': last_name,
            'user_id': user_id
        }
        self.users_info.insert_one(user)
        self.init_users_activity(user_id)

    def init_users_activity(self, user_id):
        activity = {
            'user_id': user_id,
            'purchases': [],
            'debts': {}
        }
        self.users_activity.insert_one(activity)