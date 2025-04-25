'''Handling database related tasks by defining methods from class DatabaseInterface'''

from database_interface import DatabaseInterface
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy import create_engine, URL
from datetime import datetime
from database_sql_struct import Users, RobotParts, CustomBots, CustomBotParts, Order


class SQLiteDataManager(DatabaseInterface):
    # Create
    def __init__(self, db_file_name):
        try:
            self._url_obj = URL.create(
                drivername="sqlite",
                database=db_file_name
            )
            self._engine = create_engine(self._url_obj)
        except Exception as err:
            print("Cannot initiate SQLiteDataManager" + str(err))

    def add_user(self, users_list):
        '''
        users_list is a list of users dictionaries
        users_list = [{username:"Kyle", email:"...",...
        },{username:"Karla", email:"...",...}]
        '''
        if users_list and isinstance(users_list, list):
            with Session(self._engine) as session:
                new_users_to_db_list = [
                    Users(
                        username=user["username"],
                        email=user["email"],
                        password=user["password"],
                        created_at=datetime.now()
                    ) for user in users_list
                ]
                session.add_all(new_users_to_db_list)
                session.commit()
                return True
        else:
            print("empty users_list or invalid data format!")
            return None

    def add_part(self, parts_list):
        '''
        parts_list is a list of part dict. can multiple parts to
        batch add

        parts_list = [{name:"robot_mech_arm", type:"arm",...
        },{name:, type:"...",...}]
        :param part_infos:
        :return:
        '''
        if parts_list and isinstance(parts_list, list):
            with Session(self._engine) as session:
                new_parts_list = [
                    RobotParts(name=part["name"], type=part["type"],
                               # arm, shoulder, chest, skirt, leg, foot, backpack
                               model_path=part["model_path"],
                               img_path=part["img_path"],
                               price=part["price"]
                               ) for part in parts_list
                ]
                session.add_all(new_parts_list)
                session.commit()
                return True
        else:
            print("empty parts_list or invalid data format!")
            return None

    def create_custom_bot_for_user(self, user_id, bots_list):
        '''
        bots_list is a list of bots dict. can multiple bots to
        batch add to an user
        :param user_id:
        :param bots_list:
        :return:
        '''
        # check if user_id exists
        with Session(self._engine) as session:
            stmt = select(Users).where(Users.id == user_id)
            select_result = session.scalars(stmt)
            if not select_result:
                print("No user found!")
                return False
            else:
                for user in select_result:
                    print(user.username)

    # Read
    # Update
    # Delete


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
'''

data_manager.create_custom_bot_for_user(2,[])