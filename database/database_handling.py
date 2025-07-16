import os

'''
Handling database related tasks by
defining methods from class DatabaseInterface
'''

from database.crud.crud_create import add_part, add_user, create_custom_bot_for_user, add_part_to_custom_bot, \
    create_part_type_metadata, add_order
from database.crud.crud_read import get_user, get_custom_bot, get_part, get_order, get_parts_from_custom_bot, \
    get_part_paginated, get_login_user, get_current_login_user_info, get_all_part_type_metadata
from database.crud.crud_update import update_user, update_order, update_custom_bot, update_bot_part, \
    update_part_on_custom_bot
from database.crud.crud_delete import delete_user, delete_order, delete_part_from_custom_bot, delete_robot_part, \
    delete_custom_bot_from_user
from database.database_interface import DatabaseInterface
from sqlalchemy import create_engine, URL


class SQLiteDataManager(DatabaseInterface):
    # Create

    def __init__(self, db_file_name):
        try:
            self._url_obj = URL.create(
                drivername="sqlite",
                database=db_file_name
            )
            self._engine = create_engine(os.getenv("db_uri", self._url_obj))
        except Exception as err:
            print("Cannot initiate SQLiteDataManager" + str(err))

    def add_user(self, users_list):
        return add_user(self._engine, users_list)

    def add_part(self, parts_list):
        return add_part(self._engine, parts_list)

    def create_custom_bot_for_user(self, bots_list):
        return create_custom_bot_for_user(self._engine, bots_list)

    def add_part_to_custom_bot(self, part_id, custom_robot_id, amount, direction):
        return add_part_to_custom_bot(self._engine, part_id, custom_robot_id, amount, direction)

    def create_part_type_metadata(self, part_type, is_asym):
        return create_part_type_metadata(self._engine, part_type, is_asym)

    def add_order(self, orders_list):
        return add_order(self._engine, orders_list)

    # Read
    def get_all_part_type_metadata(self):
        return get_all_part_type_metadata(self._engine)

    def get_current_login_user_info(self, user_id):
        return get_current_login_user_info(self._engine, user_id)

    def get_user(self, **criteria):
        return get_user(self._engine, **criteria)

    def get_login_user(self, email, password):
        return get_login_user(self._engine, email, password)

    def get_custom_bot(self, **criteria):
        return get_custom_bot(self._engine, **criteria)

    def get_part(self, **criteria):
        return get_part(self._engine, **criteria)

    def get_order(self, **criteria):
        return get_order(self._engine, **criteria)

    def get_parts_from_custom_bot(self, custom_robot_id):
        return get_parts_from_custom_bot(self._engine, custom_robot_id)

    def get_part_paginated(self, page, page_size, exclude_ids, **criteria):
        return get_part_paginated(self._engine, page, page_size, exclude_ids, **criteria)

    # Update
    def update_user(self, user_id, **changes):
        return update_user(self._engine, user_id, **changes)

    def update_order(self, order_id, **changes):
        return update_order(self._engine, order_id, **changes)

    def update_custom_bot(self, bot_id, **changes):
        return update_custom_bot(self._engine, bot_id, **changes)

    def update_bot_part(self, part_id, **changes):
        return update_bot_part(self._engine, part_id, **changes)

    def update_part_on_custom_bot(self, custom_robot_id, new_part_id, direction, amount):
        return update_part_on_custom_bot(self._engine, custom_robot_id, new_part_id, direction, amount)

    # Delete

    def delete_user(self, user_id):
        return delete_user(self._engine, user_id)

    def delete_custom_bot_from_user(self, user_id, bot_id):
        return delete_custom_bot_from_user(self._engine, user_id, bot_id)

    def delete_robot_part(self, part_id: int):
        return delete_robot_part(self._engine, part_id)

    def delete_part_from_custom_bot(self, bot_id: int, part_id: int, direction: str):
        return delete_part_from_custom_bot(self._engine, bot_id, part_id, direction)

    def delete_order(self, order_id: int):
        return delete_order(self._engine, order_id)


data_manager = SQLiteDataManager("custom_bot_db")

'''
data_manager.add_user([{"username": "max",
                        "email": "max.mustermann@gmail.com",
                        "password": "dfjkdjfd0ofjdfojf"}])
data_manager.add_part([{"name": "oberlisk_arm",
                        "type": "arm",
                        "model_path": "model_path_example",
                        "img_path": "img_path_example",
                        "price": 1000
                        }])
data_manager.create_custom_bot_for_user([{"user_id": 1,
                                          "name": "Autobot",
                                          }])

data_manager.add_part_to_custom_bot(1, 1, 2)
data_manager.add_order([{
    "user_id": 1,
    "custom_robot_id": 1,
    "quantity": 2,
    "status": "pending"}])

print(data_manager.get_user(id=1))
print(data_manager.get_user(id=1, username="max"))
print(data_manager.get_custom_bot(id=1))
print(data_manager.get_custom_bot(name="Autobot"))
print(data_manager.get_part(id=1, name="oberlisk_arm", type="arm"))
print(data_manager.get_order(id=1, user_id=1, status="pending"))
data_manager.update_user(1, email="maximus@yahoo.com")
data_manager.update_custom_bot(1, name="oberlisk_gundam")
data_manager.update_bot_part(part_id=1, price=200)
data_manager.update_order(1, shipping_address="yo momma house")

print(data_manager.get_parts_from_custom_bot(custom_robot_id=1))
print(data_manager.get_order(custom_robot_id = 1))
print(data_manager.update_bot_part(part_id=1, price=10))
print(data_manager.get_parts_from_custom_bot(custom_robot_id=1))
print(data_manager.get_order(id=1))
data_manager.delete_user(user_id=1)
data_manager.get_order(id=1)
'''
