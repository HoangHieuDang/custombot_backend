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
        Adds a list of users to the database.

        Args:
            users_list (list of dict): Each dictionary must contain:
                - 'username' (str): Username of the user.
                - 'email' (str): Email address of the user.
                - 'password' (str): Password of the user.

        Returns:
            bool:
                - True if all valid users were successfully added.
                - False if any error occurs during the process.

        Notes:
            - Validates the input format.
            - Skips any invalid user data without stopping the entire process.
        '''
        if not users_list or not isinstance(users_list, list):
            print("users_list is empty or not a valid list!")
            return False

        with Session(self._engine) as session:
            for user in users_list:
                try:
                    # Basic validation for required fields
                    if not all(k in user for k in ("username", "email", "password")):
                        print(f"Missing fields in user data: {user}. Skipping.")
                        continue

                    # Optionally, you can validate email format here if you want (simple regex or library)

                    new_user = Users(
                        username=user["username"],
                        email=user["email"],
                        password=user["password"],
                        created_at=datetime.now()
                    )

                    session.add(new_user)
                    session.commit()
                    print(f"User {user['username']} added successfully!")

                except Exception as e:
                    print(f"Cannot add user {user.get('username', 'unknown')}: {e}")
                    session.rollback()
                    continue  # Try adding the next user instead of failing the whole process

        return True

    def add_part(self, parts_list):
        '''
        parts_list is a list of part dicts.
        Example:
            parts_list = [
                {"name": "robot_mech_arm", "type": "arm", "model_path": "...", "img_path": "...", "price": 100},
                {"name": "robot_leg", "type": "leg", "model_path": "...", "img_path": "...", "price": 150}
            ]
        Returns:
            True if parts were successfully added, False otherwise.
        '''
        if parts_list and isinstance(parts_list, list):
            with Session(self._engine) as session:
                new_parts_list = []
                try:
                    for part in parts_list:
                        # Validate critical fields
                        if not all(k in part for k in ("name", "type", "model_path", "img_path", "price")):
                            print(f"Missing required fields in part: {part}")
                            continue  # Skip incomplete part

                        # Validate price is a number
                        if not isinstance(part["price"], (int, float)):
                            print(f"Invalid price type for part: {part}")
                            continue

                        new_part = RobotParts(
                            name=part["name"],
                            type=part["type"],  # arm, shoulder, chest, skirt, leg, foot, backpack
                            model_path=part["model_path"],
                            img_path=part["img_path"],
                            price=part["price"]
                        )
                        new_parts_list.append(new_part)

                    if new_parts_list:
                        session.add_all(new_parts_list)
                        session.commit()
                        print(f"Successfully added {len(new_parts_list)} parts.")
                        return True
                    else:
                        print("No valid parts to add.")
                        return False

                except Exception as e:
                    session.rollback()
                    print(f"Failed to add parts due to error: {e}")
                    return False
        else:
            print("Empty parts_list or invalid data format!")
            return False

    def create_custom_bot_for_user(self, bots_list):
        '''
        Creates custom bots for users and adds them to the database.

        Args:
            bots_list (list): A list of dictionaries. Each dictionary must contain:
                - 'user_id' (int): Foreign key referencing the user.
                - 'name' (str): Name of the custom bot.
        Returns:
            bool:
                - True if at least one bot was successfully added.
                - False if no valid bots were added or an error occurred.
        '''
        if not bots_list or not isinstance(bots_list, list):
            print("Empty bots_list or invalid data format!")
            return False

        with Session(self._engine) as session:
            new_bots_list = []

            for bot in bots_list:
                # Validate required fields
                if not all(k in bot for k in ("user_id", "name")):
                    print(f"Missing required fields in bot data: {bot}")
                    continue

                # Check if user exists
                stmt = select(Users).where(Users.id == bot["user_id"])
                user = session.scalar(stmt)
                if not user:
                    print(f"No user found for user_id {bot['user_id']}, skipping.")
                    continue

                # Create new CustomBot instance
                try:
                    new_bot = CustomBots(
                        user_id=bot["user_id"],
                        name=bot["name"],
                        status="in_progress",  # Default to 'in_progress'
                        created_at=datetime.now(),
                        total_price=0
                        # Total_price is initially 0, when parts are added, the total_price will be recalculated and updated
                    )
                    new_bots_list.append(new_bot)
                except Exception as e:
                    print(f"Error creating CustomBot object: {e}")
                    continue

            # If at least one valid bot to add
            if new_bots_list:
                try:
                    session.add_all(new_bots_list)
                    session.commit()
                    print(f"Successfully added {len(new_bots_list)} custom bots.")
                    return True
                except Exception as e:
                    print(f"Error committing bots to database: {e}")
                    session.rollback()
                    return False
            else:
                print("No valid bots to add.")
                return False

    def add_part_to_custom_bot(self, part_id, custom_robot_id):
        """
        Adds a robot part to a custom bot by inserting a new entry
        into the CustomBotParts association table and updates the custom bot's total price.

        Args:
            part_id (int): The ID of the robot part to be added.
            custom_robot_id (int): The ID of the custom bot to which the part will be added.

        Returns:
            bool:
                - True if the part was successfully added and total price updated.
                - False if either the part_id or custom_bot_id does not exist in the database.

        Notes:
            - Assumes that part_id and bot_id must already exist in their respective tables.
            - Commits the transaction immediately after adding the entry and updating the price.
        """
        with Session(self._engine) as session:
            # Check if part_id exists
            part = session.scalar(select(RobotParts).where(RobotParts.id == part_id))
            if not part:
                print(f"No part found for part_id {part_id}")
                return False

            # Check if bot_id exists
            bot = session.scalar(select(CustomBots).where(CustomBots.id == custom_robot_id))
            if not bot:
                print(f"No bot found for bot_id {custom_robot_id}")
                return False

            # Add part_id and bot_id into CustomBotParts table and update total_price
            try:
                session.add(CustomBotParts(
                    robot_part_id=part_id,
                    custom_robot_id=custom_robot_id
                ))

                # Update the custom bot's total_price
                if bot.total_price is None:
                    bot.total_price = 0
                bot.total_price += part.price

                session.commit()
                print(f"Part with part_id {part_id} was added to custom bot with bot_id {custom_robot_id}")
                print(f"Updated total_price of custom bot (id={custom_robot_id}) to {bot.total_price}")
                return True
            except Exception as e:
                session.rollback()
                print(f"Failed to add part to custom bot: {e}")
                return False

    def add_order(self, orders_list):
        '''
        Adds a list of orders to the database, each order containing a user ID
        and a custom bot ID. Calculates total price based on bot's price and quantity.
        Also updates the custom bot status to "ordered" once the order is placed.

        Args:
            orders_list (list of dict): A list of dictionaries where each dictionary
                                        contains the details of an order.
                                        Each dictionary must have the following keys:
                                        - 'user_id': The ID of the user placing the order.
                                        - 'custom_robot_id': The ID of the custom bot being ordered.
                                        - 'quantity' (optional): Number of bots ordered (default 1).
        Returns:
            bool:
                - True if all valid orders were successfully added to the database.
                - False if any errors occurred while adding an order.
        Notes:
            - For each order, checks if the user and custom bot exist in the database.
            - Calculates the total_price automatically.
            - Updates the custom bot status to "ordered".
            - Continues processing the rest of the orders even if one fails.
        '''
        if not orders_list or not isinstance(orders_list, list):
            print("orders_list is empty or not a valid list!")
            return False

        with Session(self._engine) as session:
            for order in orders_list:
                try:
                    # Validate user
                    user_query = select(Users).where(Users.id == order["user_id"])
                    user = session.scalar(user_query)
                    if not user:
                        print(f"User with user_id {order['user_id']} doesn't exist in User database!")
                        continue

                    # Validate custom bot
                    bot_query = select(CustomBots).where(CustomBots.id == order["custom_robot_id"])
                    bot = session.scalar(bot_query)
                    if not bot:
                        print(
                            f"Custom bot with custom_robot_id {order['custom_robot_id']} doesn't exist in Custom Bot database!")
                        continue

                    # Get quantity (default to 1 if not provided)
                    quantity = order.get('quantity', 1)
                    if not isinstance(quantity, int) or quantity <= 0:
                        print(f"Invalid quantity provided for order: {order}. Skipping.")
                        continue

                    # Calculate total price
                    total_price = bot.total_price * quantity

                    # Create the Order
                    new_order = Order(
                        user_id=order['user_id'],
                        custom_robot_id=order['custom_robot_id'],
                        quantity=quantity,
                        total_price=total_price,
                        status=order.get('status', 'pending'),  # Default status to 'pending'
                        payment_method=order.get('payment_method', None),
                        shipping_address=order.get('shipping_address', None),
                        shipping_date=order.get('shipping_date', None),
                        created_at=datetime.now()
                    )

                    session.add(new_order)

                    # Update the CustomBot status to "ordered"
                    bot.status = "ordered"

                    session.commit()
                    print(f"Order added successfully! Bot ID {bot.id} status updated to 'ordered'.")

                except Exception as e:
                    print(f"Cannot add order due to error: {e}")
                    session.rollback()
                    continue  # Try the next order even if one fails

        return True


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
data_manager.create_custom_bot_for_user([{"user_id": 1,
                                          "name": "Autobot",
                                        ])
data_manager.add_part_to_custom_bot(2,2)

data_manager.add_order([{
    "user_id": 1,
    "custom_robot_id": 1,
    "quantity": 2,
    "status":"pending",
}])
'''
