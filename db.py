import os
import collections
from datetime import datetime
from pymongo import MongoClient

# from dotenv import load_dotenv

# BASEDIR = os.path.abspath(os.path.dirname(__file__))
# load_dotenv(os.path.join(BASEDIR, 'dev.env'))

class MongoDbContext:
    """Mongo database context class"""

    def __init__(self):
        self.connection_string = os.getenv('CONNECTION_STRING')
        self.client = MongoClient(self.connection_string)
        self.db = self.client[os.getenv('DB_NAME')]

    def check_and_add_user(self, message):
        if self.db.users.find_one({'user_id': message.from_user.id}) == None:
            new_user = {
                'first_name': message.from_user.first_name,
                'last_name': message.from_user.last_name,
                'user_id': message.from_user.id,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'state': 0
            }
            self.db.users.insert_one(new_user)
        return

    def get_state(self, message):
        user_id = message.from_user.id
        user = self.db.users.find_one({'user_id': user_id})
        return user['state']

    def set_state(self, message, state_value):
        user_id = message.from_user.id
        self.db.users.update_one({'user_id': user_id}, {"$set": {'state': state_value}})

    def get_storage(self):
        storage = self.db.storage.find()
        return storage

    def set_storage(self, message, new_poi):
        new_poi = {
            'current_location': new_poi.get('current_location'),
            'selected_location': new_poi.get('selected_location'),
            'name': new_poi.get('name'),
            'photo_id': new_poi.get('photo'),
            'user_id': message.from_user.id,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.db.storage.insert_one(new_poi)
        return


if __name__ == '__main__':
    cols = ['id', 'first_name', 'last_name']
    User = collections.namedtuple('User', cols)
    from_user = User(1, 'Петр', 'Сидоров')
    from_user.first_name
    Message = collections.namedtuple('Message', 'from_user')
    message = Message(from_user)

    mongo = MongoDbContext()
    mongo.check_and_add_user(message)