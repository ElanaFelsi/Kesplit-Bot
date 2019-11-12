from model import DB

db = DB('1234', 'Hackthon Winners')
db.insert_user_info('Elana', '1')
db.insert_user_info('Miriam', '2')
db.insert_user_info('Hadass', '3')


db1 = DB('4321', 'checking')
db1.insert_user_info('Shalom', '1')