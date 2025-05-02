'''Handling database related tasks by defining methods from class DatabaseInterface'''
from database_interface import DatabaseInterface
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, delete
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

    def add_part_to_custom_bot(self, part_id, custom_robot_id, amount):
        """
        Adds a robot part to a custom bot by inserting or updating an entry
        in the CustomBotParts association table.

        Only allows modification if the custom bot is still in 'in_progress' status.

        Args:
            part_id (int): The ID of the robot part to be added.
            custom_robot_id (int): The ID of the custom bot to which the part will be added.
            amount (int): The quantity of the part to add (must be >= 1).

        Returns:
            bool: True if successful, False otherwise.
        """
        with Session(self._engine) as session:
            # Validate amount
            if not isinstance(amount, int) or amount < 1:
                print("Amount must be a positive integer >= 1.")
                return False

            # Validate part
            part = session.scalar(select(RobotParts).where(RobotParts.id == part_id))
            if not part:
                print(f"No part found with part_id {part_id}.")
                return False

            # Validate custom bot
            bot = session.scalar(select(CustomBots).where(CustomBots.id == custom_robot_id))
            if not bot:
                print(f"No custom bot found with id {custom_robot_id}.")
                return False

            if bot.status == "ordered":
                print(f"Cannot modify bot '{bot.name}' (ID {custom_robot_id}) because it has already been ordered.")
                return False

            try:
                # Check if the part is already in the bot
                existing_entry = session.scalar(
                    select(CustomBotParts)
                    .where(
                        CustomBotParts.robot_part_id == part_id,
                        CustomBotParts.custom_robot_id == custom_robot_id
                    )
                )

                if existing_entry:
                    # If already exists, update the amount
                    existing_entry.robot_part_amount += amount
                    print(f"Updated part amount for part_id {part_id} in bot_id {custom_robot_id}.")
                else:
                    # Otherwise, insert new part
                    session.add(CustomBotParts(
                        robot_part_id=part_id,
                        custom_robot_id=custom_robot_id,
                        robot_part_amount=amount
                    ))
                    print(f"Added part_id {part_id} to bot_id {custom_robot_id}.")

                session.commit()
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
        '''
        if not orders_list or not isinstance(orders_list, list):
            print("orders_list is empty or not a valid list!")
            return False

        with Session(self._engine) as session:
            for order in orders_list:
                try:
                    # Validate user
                    user = session.scalar(select(Users).where(Users.id == order["user_id"]))
                    if not user:
                        print(f"User with user_id {order['user_id']} doesn't exist!")
                        continue

                    # Validate custom bot
                    bot = session.scalar(select(CustomBots).where(CustomBots.id == order["custom_robot_id"]))
                    if not bot:
                        print(f"Custom bot with id {order['custom_robot_id']} doesn't exist!")
                        continue

                    # Check that the bot has at least one part
                    part_exists = session.scalar(
                        select(func.count()).select_from(CustomBotParts)
                        .where(CustomBotParts.custom_robot_id == order["custom_robot_id"])
                    )
                    if not part_exists:
                        print(f"Custom bot with id {order['custom_robot_id']} has no parts!")
                        continue

                    # Get quantity
                    quantity = order.get('quantity', 1)
                    if not isinstance(quantity, int) or quantity <= 0:
                        print(f"Invalid quantity for order: {order}")
                        continue

                    # Calculate price of one bot
                    bot_price = session.scalar(
                        select(func.sum(RobotParts.price * CustomBotParts.robot_part_amount))
                        .select_from(CustomBotParts)
                        .join(RobotParts, RobotParts.id == CustomBotParts.robot_part_id)
                        .where(CustomBotParts.custom_robot_id == order["custom_robot_id"])
                    )

                    if bot_price is None:
                        print(f"[Warning] Price calculation failed for bot id={order['custom_robot_id']}.")
                        continue

                    total_price = quantity * bot_price

                    # Create order
                    new_order = Order(
                        user_id=order['user_id'],
                        custom_robot_id=order['custom_robot_id'],
                        quantity=quantity,
                        total_price=total_price,
                        status=order.get('status', 'pending'),
                        payment_method=order.get('payment_method'),
                        shipping_address=order.get('shipping_address'),
                        shipping_date=order.get('shipping_date'),
                        created_at=datetime.now()
                    )

                    session.add(new_order)
                    bot.status = "ordered"
                    session.commit()
                    print(f"[Success] Order added. Bot ID {bot.id} marked as 'ordered'.")

                except Exception as e:
                    print(f"[Error] Failed to add order: {e}")
                    session.rollback()
                    continue

        return True

    # Read
    def get_user(self, **criteria):
        """
        Retrieves a user from the database based on dynamic search criteria.

        Args:
            **criteria (dict): A variable-length argument list of key-value pairs used
                                to filter the users. The valid keys (filters) are:
                                - 'id': The unique identifier of the user.
                                - 'email': The email address of the user.
                                - 'username': The username of the user.
                                - 'created_at': The creation date of the user account.

        Returns:
            dict or bool:
                - If a user matching the criteria is found, a dictionary containing
                  the user's information is returned with the following keys:
                    - 'id': The unique identifier of the user.
                    - 'username': The username of the user.
                    - 'created_at': The creation date and time of the user account.
                - If no matching user is found, `False` is returned.
                - If an invalid filter criterion is provided, `False` is returned.
                - If no criteria are provided, a message is printed and `False` is returned.

        Raises:
            Exception: If the database query fails or other exceptions occur.

        Example:
            get_user(id=1, email="tom@example.com")
            get_user(username="tom", created_at="2025-01-01")

        Notes:
            - The function checks if the provided filters are valid and ensures that
              only known attributes (`id`, `email`, `username`, `created_at`) are used.
            - Multiple search criteria can be combined (AND logic).
            - If the provided criteria match an existing user, their details are returned.
            - If no matching user is found or an error occurs, appropriate messages
              are printed for debugging purposes.
        """
        possible_filters = {"id", "email", "username", "created_at"}

        if not criteria:
            print("No search criteria provided!")
            return False

        with Session(self._engine) as session:
            # Initialize an empty list to hold filter conditions
            filter_conditions = []

            # Loop over criteria and add filters to the list
            for attr, value in criteria.items():
                if attr in possible_filters:
                    try:
                        sql_column_attr = getattr(Users, attr)
                        filter_conditions.append(sql_column_attr.__eq__(value))  # Add each condition

                    except Exception as e:
                        print(f"Error while processing filter '{attr}': {str(e)}")
                        return False
                else:
                    print(f"Filter '{attr}' is not allowed!")
                    return False

            # If no valid filters were added, return False
            if not filter_conditions:
                print("No valid filters provided!")
                return False

            # Combine the filter conditions with AND logic
            combined_filter = filter_conditions.pop(0)  # pop the first item of the list to start the chained condition
            for condition in filter_conditions:
                # concatenate the conditions together into a combined_filter
                combined_filter = combined_filter & condition

            try:
                # Execute the query with combined filter conditions
                query = select(Users).where(combined_filter)
                # get all query results
                result = session.scalars(query).all()
                if result:
                    return [{
                        "id": row.id,
                        "username": row.username,
                        "email": row.email,
                        "created_at": row.created_at
                    } for row in result]
                else:
                    print("No user found matching the given criteria.")
                    return False

            except Exception as e:
                print("SQL query not successful! " + str(e))
                return False

    def get_custom_bot(self, **criteria):
        """
        Retrieves a custom bot from the database based on dynamic search criteria.

        Args:
            **criteria (dict): A variable-length argument list of key-value pairs used
                                to filter the custom bots. The valid keys (filters) are:
                                - 'id': The unique identifier of the custom bot.
                                - 'user_id': The ID of the user associated with the custom bot.
                                - 'name': The name of the custom bot.
                                - 'status': The status of the custom bot (e.g., 'in_progress', 'ordered').
                                - 'created_at': The creation date of the custom bot.


        Returns:
            list of dict or bool:
                - If custom bots matching the criteria are found, a list of dictionaries is returned.
                  Each dictionary contains the following keys:
                    - 'id'
                    - 'user_id'
                    - 'name'
                    - 'status'
                    - 'total_price'
                    - 'created_at'
                - If no matching custom bot is found, `False` is returned.
                - If an invalid filter criterion is provided, `False` is returned.
                - If no criteria are provided, a message is printed and `False` is returned.

        Raises:
            Exception: If the database query fails or other exceptions occur.

        Example:
            get_custom_bot(id=1, status="ordered")
            get_custom_bot(name="RoboMaster", user_id=2)

        Notes:
            - Only valid filters are allowed.
            - Multiple search criteria are combined with AND logic.
            - If no matching bots are found or an error occurs, a helpful message is printed.
        """
        possible_filters = {"id", "user_id", "name", "status", "created_at"}

        if not criteria:
            print("No search criteria provided!")
            return False

        with Session(self._engine) as session:
            filter_conditions = []

            for attr, value in criteria.items():
                if attr in possible_filters:
                    try:
                        sql_column_attr = getattr(CustomBots, attr)
                        filter_conditions.append(sql_column_attr == value)
                    except Exception as e:
                        print(f"Error while processing filter '{attr}': {str(e)}")
                        return False
                else:
                    print(f"Filter '{attr}' is not allowed!")
                    return False

            if not filter_conditions:
                print("No valid filters provided!")
                return False

            combined_filter = filter_conditions.pop(0)
            for condition in filter_conditions:
                combined_filter = combined_filter & condition

            try:
                query = select(CustomBots).where(combined_filter)
                result = session.scalars(query).all()

                if result:
                    return [{
                        "id": row.id,
                        "user_id": row.user_id,
                        "name": row.name,
                        "status": row.status,
                        "created_at": row.created_at
                    } for row in result]
                else:
                    print("No custom bot found matching the given criteria.")
                    return False

            except Exception as e:
                print("SQL query not successful! " + str(e))
                return False

    def get_part(self, **criteria):
        """
        Retrieves a part from the database based on dynamic search criteria.

        Args:
            **criteria (dict): A variable-length argument list of key-value pairs used
                                to filter the parts. The valid keys (filters) are:
                                - 'id': The unique identifier of the part.
                                - 'name': The name of the part.
                                - 'type': The type/category of the part.
                                - 'price': The price of the part.

        Returns:
            list of dict or bool:
                - If parts matching the criteria are found, a list of dictionaries is returned.
                  Each dictionary contains the following keys:
                    - 'id'
                    - 'user_id'
                    - 'name'
                    - 'status'
                    - 'total_price'
                    - 'created_at'
                - If no matching part is found, `False` is returned.
                - If an invalid filter criterion is provided, `False` is returned.
                - If no criteria are provided, a message is printed and `False` is returned.

        Raises:
            Exception: If the database query fails or other exceptions occur.

        Example:
            get_part(id=1, name="Backpack")
            get_part(type="shoulder", price=19.99)

        Notes:
            - Only valid filters are allowed.
            - Multiple search criteria are combined with AND logic.
            - If no matching parts are found or an error occurs, a helpful message is printed.
        """
        possible_filters = {"id", "name", "type", "price"}

        if not criteria:
            print("No search criteria provided!")
            return False

        with Session(self._engine) as session:
            filter_conditions = []

            for attr, value in criteria.items():
                if attr in possible_filters:
                    try:
                        sql_column_attr = getattr(RobotParts, attr)
                        filter_conditions.append(sql_column_attr == value)
                    except Exception as e:
                        print(f"Error while processing filter '{attr}': {str(e)}")
                        return False
                else:
                    print(f"Filter '{attr}' is not allowed!")
                    return False

            if not filter_conditions:
                print("No valid filters provided!")
                return False
            # combine all appended condition into a chained condition with AND logic
            # take the first element from the filtered_conditions list for the chained condition variable combined_filter
            combined_filter = filter_conditions.pop(0)
            for condition in filter_conditions:
                # concatenate the conditions together using AND logic
                combined_filter = combined_filter & condition

            try:
                query = select(RobotParts).where(combined_filter)
                result = session.scalars(query).all()

                if result:
                    return [{
                        "id": row.id,
                        "name": row.name,
                        "type": row.type,
                        "model_path": row.model_path,
                        "img_path": row.img_path,
                        "price": row.price
                    } for row in result]
                else:
                    print("No part found matching the given criteria.")
                    return False

            except Exception as e:
                print("SQL query not successful! " + str(e))
                return False

    def get_order(self, **criteria):
        """
        Retrieves an order from the database based on dynamic search criteria.

        Args:
            **criteria (dict): A variable-length argument list of key-value pairs used
                                to filter the orders. The valid keys (filters) are:
                                - 'id'
                                - 'user_id'
                                - 'custom_robot_id'
                                - 'quantity'
                                - 'total_price'
                                - 'status'
                                - 'payment_method'
                                - 'shipping_address'
                                - 'shipping_date'
                                - 'created_at'

        Returns:
            list of dict or bool:
                - If orders matching the criteria are found, a list of dictionaries is returned.
                  Each dictionary contains the following keys:
                    - 'id'
                    - 'user_id'
                    - 'custom_robot_id'
                    - 'quantity'
                    - 'total_price'
                    - 'status'
                    - 'payment_method'
                    - 'shipping_address'
                    - 'shipping_date'
                    - 'created_at'
                - If no matching order is found, `False` is returned.
                - If an invalid filter criterion is provided, `False` is returned.
                - If no criteria are provided, a message is printed and `False` is returned.

        Raises:
            Exception: If the database query fails or other exceptions occur.

        Example:
            get_order(id=1, user_id=5, status="pending")

        Notes:
            - Only valid filters are allowed.
            - Multiple search criteria combined with AND logic.
            - If no matching orders are found or an error occurs, a helpful message is printed.
        """
        possible_filters = {
            "id", "user_id", "custom_robot_id", "quantity",
            "total_price", "status", "payment_method",
            "shipping_address", "shipping_date", "created_at"
        }

        if not criteria:
            print("No search criteria provided!")
            return False

        with Session(self._engine) as session:
            filter_conditions = []

            for attr, value in criteria.items():
                if attr in possible_filters:
                    try:
                        sql_column_attr = getattr(Order, attr)
                        filter_conditions.append(sql_column_attr == value)
                    except Exception as e:
                        print(f"Error while processing filter '{attr}': {str(e)}")
                        return False
                else:
                    print(f"Filter '{attr}' is not allowed!")
                    return False

            if not filter_conditions:
                print("No valid filters provided!")
                return False

            combined_filter = filter_conditions.pop(0)
            for condition in filter_conditions:
                combined_filter = combined_filter & condition

            try:
                query = select(Order).where(combined_filter)
                result = session.scalars(query).all()

                if result:
                    return [{
                        "id": row.id,
                        "user_id": row.user_id,
                        "custom_robot_id": row.custom_robot_id,
                        "quantity": row.quantity,
                        "total_price": row.total_price,
                        "status": row.status,
                        "payment_method": row.payment_method,
                        "shipping_address": row.shipping_address,
                        "shipping_date": row.shipping_date,
                        "created_at": row.created_at
                    } for row in result]
                else:
                    print("No order found matching the given criteria.")
                    return False

            except Exception as e:
                print("SQL query not successful! " + str(e))
                return False

    def get_parts_from_custom_bot(self, custom_robot_id):
        """
        Retrieves a list of robot parts associated with a given custom robot.

        Args:
            custom_robot_id (int): The unique identifier of the custom robot whose parts are to be fetched.

        Returns:
            list of dicts or bool:
                - If the custom robot has parts associated with it, a list of dictionaries is returned.
                  Each dictionary contains the following keys:
                    - 'custom_robot_id': The unique identifier of the custom robot.
                    - 'robot_part_id': The unique identifier of the robot part.
                    - 'part_name': The name of the robot part.
                    - 'part_type': The type of the robot part (e.g., 'arm', 'leg', etc.).
                    - 'part_price': The price of the robot part.
                    - 'part_amount': The amount of each part
                    - 'part_model_path': The file path to the model of the part.
                    - 'part_img_path': The file path to the image of the part.
                - If no robot parts are found, `False` is returned.
                - If invalid `custom_robot_id` is provided, `False` is returned.
                - If there are errors during the database query, `False` is returned.

        Raises:
            Exception: If the database query fails or any unexpected errors occur during execution.

        Example:
            get_parts_from_custom_bot(1)

        Notes:
            - The function retrieves parts from the `CustomBotParts` table based on the `custom_robot_id`.
            - It joins the `CustomBotParts` and `RobotParts` tables to return not only the robot part IDs but also the relevant part details.
            - The returned list will include details such as the part's name, type, price, model file path, and image path.
        """
        if not custom_robot_id or not isinstance(custom_robot_id, int):
            print("not valid search criteria!")
            return False
        with Session(self._engine) as session:
            try:
                # join CustomBotParts and RobotParts Tables together
                # where the CustomBotParts.custom_robot_id == custom_robot_id
                query = (
                    select(
                        CustomBotParts.custom_robot_id,
                        CustomBots.name.label("custom_bot_name"),
                        CustomBots.user_id.label("user_id"),
                        RobotParts.id.label("robot_part_id"),
                        RobotParts.name.label("robot_part_name"),
                        RobotParts.type,
                        RobotParts.price,
                        CustomBotParts.robot_part_amount,
                        RobotParts.model_path,
                        RobotParts.img_path
                    )
                    .join(CustomBots, CustomBotParts.custom_robot_id == CustomBots.id)
                    .join(RobotParts, CustomBotParts.robot_part_id == RobotParts.id)
                    .where(CustomBotParts.custom_robot_id == custom_robot_id)
                )

                # session.scalars.all() returns only one column and only work best when we use the entire table model
                # such as select(Users), while picking specific columns to display, scalars will not work as expected
                # scalars will try to flatten to multiple columns and lead to weird results
                # session.execute on the other returns all columns and rows as it should be

                result = session.execute(query).all()
                if result:
                    return [{
                        "custom_robot_id": row.custom_robot_id,
                        "user_id": row.user_id,
                        "custom_bot_name": row.custom_bot_name,
                        "robot_part_id": row.robot_part_id,
                        "robot_part_name": row.robot_part_name,
                        "type": row.type,
                        "price": row.price,
                        "amount": row.robot_part_amount,
                        "model_path": row.model_path,
                        "img_path": row.img_path
                    } for row in result]
                else:
                    print("No parts found for the given custom robot ID.")
                    return False


            except Exception as e:
                print("Error while processing filter: " + str(e))
                return False

    # Update

    def update_user(self, user_id, **changes):
        """
            Updates user attributes in the database based on the provided changes.

            Args:
                user_id (int): The unique identifier of the user to update.
                **changes (dict): A variable-length dictionary of key-value pairs representing
                                  the attributes to update and their new values. Only the following
                                  keys are allowed:
                                    - 'email': The new email address.
                                    - 'username': The new username.

            Returns:
                bool:
                    - True if the update was successful.
                    - False if an invalid attribute is provided or if an error occurs during the update.

            Raises:
                Exception: Any exceptions raised during the database transaction are caught and
                           printed to help with debugging.

            Example:
                update_user(1, email="new@example.com", username="new_name")

            Notes:
                - The function uses SQLAlchemy ORM to query and update the user.
                - Only the fields explicitly listed in `possible_changes` can be updated.
                - The update is committed to the database only if all inputs are valid.
            """
        possible_changes = {"email", "username"}
        with Session(self._engine) as session:
            for key_change, value in changes.items():
                # if key_change is valid
                if key_change in possible_changes:
                    try:
                        user = session.execute(select(Users).filter_by(id=user_id)).scalar_one()
                        setattr(user, key_change, value)
                        session.commit()
                    except Exception as e:
                        print("Sth went wrong while updating db: " + str(e))
                        return False
                else:
                    print("Invalid input attributes!")
                    return False
        return True

    def update_custom_bot(self, bot_id, **changes):
        """
        Updates the non-critical attributes of a custom robot in the database.

        Args:
            bot_id (int): The unique identifier of the custom robot to update.
            **changes (dict): Key-value pairs representing the fields to update.
                              Only the 'name' field is allowed.

        Returns:
            bool:
                - True if the update was successful.
                - False if an invalid attribute is provided or if an error occurs.

        Example:
            update_custom_bot(5, name="Battle Titan")

        Notes:
            - Only the 'name' field is allowed to be updated.
            - Status changes must be handled through the ordering process or other
              domain-specific workflows to ensure consistency across tables.
        """
        possible_changes = {"name"}
        with Session(self._engine) as session:
            for key_change, value in changes.items():
                if key_change in possible_changes:
                    try:
                        custom_bot = session.execute(select(CustomBots).filter_by(id=bot_id)).scalar_one()
                        setattr(custom_bot, key_change, value)
                        session.commit()
                    except Exception as e:
                        print("Sth went wrong while updating db: " + str(e))
                        return False
                else:
                    print("Invalid input attributes!")
                    return False
        return True

    def update_bot_part(self, part_id, **changes):
        '''
        Update one or more attributes of a robot part. If its price changes,
        recalculate total_price for orders with 'pending' status that include the updated part.
        '''
        allowed_types = {"arm", "shoulder", "chest", "skirt", "leg", "foot", "backpack"}
        possible_changes = {"name", "type", "model_path", "img_path", "price"}
        with Session(self._engine) as session:
            try:
                part = session.scalar(select(RobotParts).where(RobotParts.id == part_id))
                if not part:
                    print(f"No RobotPart found with id={part_id}")
                    return False
                price_changed = False
                original_price = part.price
                new_price = original_price
                for key, value in changes.items():
                    if key not in possible_changes:
                        print(f"Invalid attribute '{key}'—cannot update.")
                        return False
                    if key == "type" and value not in allowed_types:
                        print(f"Invalid part type '{value}'. Must be one of {allowed_types}.")
                        return False
                    if key == "price":
                        if not isinstance(value, (int, float)):
                            print(f"Invalid price value: {value!r}")
                            return False
                        price_changed = True
                        new_price = value
                    setattr(part, key, value)
                session.flush()  # Apply changes
                if price_changed and original_price != new_price:
                    try:
                        # Get all bot IDs that use this part
                        bot_ids = session.scalars(
                            select(CustomBotParts.custom_robot_id)
                            .where(CustomBotParts.robot_part_id == part_id)
                        ).all()
                        if not bot_ids:
                            print("No custom bots have the part. No updates needed.")
                        else:
                            for bot_id in set(bot_ids):
                                # Check if a pending order exists for this bot
                                pending_order = session.scalar(
                                    select(Order)
                                    .where(and_(
                                        Order.custom_robot_id == bot_id,
                                        Order.status == "pending"
                                    ))
                                )
                                if not pending_order:
                                    print(f"Bot ID {bot_id} has no pending order or isn't in the order table yet.")
                                    continue
                                # Recalculate price
                                bot_price = session.scalar(
                                    select(func.sum(RobotParts.price * CustomBotParts.robot_part_amount))
                                    .select_from(CustomBotParts)
                                    .join(RobotParts, RobotParts.id == CustomBotParts.robot_part_id)
                                    .where(CustomBotParts.custom_robot_id == bot_id)
                                )
                                if bot_price is None:
                                    print(f"[Warning] Price calculation failed for bot ID {bot_id}.")
                                    continue
                                pending_order.total_price = pending_order.quantity * bot_price
                        session.commit()
                    except Exception as e:
                        print("Error when updating affected custom bots:", e)
                        session.rollback()
                        # Revert the price
                        with Session(self._engine) as revert_session:
                            part_revert = revert_session.get(RobotParts, part_id)
                            part_revert.price = original_price
                            revert_session.commit()
                            print("reverted the part's price back to original price.")
                        return False

                session.commit()
                return True

            except Exception as e:
                session.rollback()
                print(f"Error updating robot part {part_id}: {e}")
                return False

    def update_order(self, order_id, **changes):
        """
        Update attributes of an existing order.

        Args:
            order_id (int): ID of the order to update.
            **changes: Key/value pairs of attributes to change. Allowed keys:
                - 'quantity' (int > 0)
                - 'status' (str: one of {"pending", "paid", "shipped", "cancelled"})
                - 'shipping_address' (str)
                - 'shipping_date' (str in 'YYYY-MM-DD' format or datetime.date)
                - 'payment_method' (str)

        Returns:
            bool: True if update succeeded, False otherwise.
        """
        possible_status = {"pending", "paid", "shipped", "cancelled"}
        possible_changes = {"quantity", "status", "shipping_address", "shipping_date", "payment_method"}

        with Session(self._engine) as session:
            try:
                order = session.get(Order, order_id)
                if not order:
                    print(f"No order found with ID {order_id}")
                    return False

                for key, value in changes.items():
                    if key not in possible_changes:
                        print(f"Invalid field '{key}' — cannot update.")
                        return False

                    if key == "quantity":
                        if not isinstance(value, int) or value <= 0:
                            print("Quantity must be a positive integer.")
                            return False

                    if key == "status":
                        if value not in possible_status:
                            print(f"Invalid status '{value}'. Allowed: {possible_status}")
                            return False

                    if key == "shipping_date":
                        from datetime import datetime, date
                        if isinstance(value, str):
                            # convert to datetime object
                            try:
                                value = datetime.strptime(value, "%Y-%m-%d").date()
                            except ValueError:
                                print("shipping_date must be in 'YYYY-MM-DD' format.")
                                return False
                        elif not isinstance(value, date):
                            print("shipping_date must be a string or a date object.")
                            return False

                    setattr(order, key, value)

                session.commit()
                print(f"Order {order_id} updated successfully.")
                return True

            except Exception as e:
                session.rollback()
                print(f"Error updating order {order_id}: {e}")
                return False

    # Delete

    def delete_user(self, user_id):
        """
        Delete a user and their related data, while preserving legal Order records.

        Orders with status 'paid', 'shipped', or 'cancelled' will be retained,
        and their user_id will be set to None for anonymization.

        Args:
            user_id (int): ID of the user to delete.

        Returns:
            bool: True if user deleted successfully, False otherwise.
        """
        with Session(self._engine) as session:
            try:
                user = session.get(Users, user_id)
                if not user:
                    print(f"No user found with ID {user_id}")
                    return False

                # Find all custom bots for this user
                custom_bots = session.scalars(
                    select(CustomBots).where(CustomBots.user_id == user_id)
                ).all()
                bot_ids = [bot.id for bot in custom_bots]

                if bot_ids:
                    # Separate orders that need to be preserved vs deleted
                    preserved_statuses = {"paid", "shipped", "cancelled"}
                    preserved_orders = session.scalars(
                        select(Order).where(
                            Order.custom_robot_id.in_(bot_ids),
                            Order.status.in_(preserved_statuses)
                        )
                    ).all()

                    # Set user_id to None for preserved orders
                    for order in preserved_orders:
                        order.user_id = None

                    # Delete orders that are not preserved
                    session.execute(
                        delete(Order).where(
                            Order.custom_robot_id.in_(bot_ids),
                            Order.status.not_in(preserved_statuses)
                        )
                    )

                    # Delete all parts associated with the user's custom bots
                    session.execute(
                        delete(CustomBotParts).where(CustomBotParts.custom_robot_id.in_(bot_ids))
                    )

                    # Delete the custom bots
                    session.execute(
                        delete(CustomBots).where(CustomBots.id.in_(bot_ids))
                    )

                # Finally, delete the user
                session.delete(user)
                session.commit()
                print(f"User {user_id} and associated data deleted (orders preserved if needed).")
                return True

            except Exception as e:
                session.rollback()
                print(f"Error deleting user {user_id}: {e}")
                return False

    def delete_custom_bot_from_user(self, user_id, bot_id):
        """
        Delete a custom bot belonging to a user, only if it is still in 'in_progress' status.

        Args:
            user_id (int): ID of the user.
            bot_id (int): ID of the custom bot.

        Returns:
            bool: True if the deletion was successful, False otherwise.
        """
        with Session(self._engine) as session:
            try:
                bot = session.get(CustomBots, bot_id)

                if not bot:
                    print(f"No bot found with ID {bot_id}")
                    return False

                if bot.user_id != user_id:
                    print(f"Bot {bot_id} does not belong to user {user_id}")
                    return False

                if bot.status != "in_progress":
                    print(f"Cannot delete bot {bot_id} — status is '{bot.status}', not 'in_progress'")
                    return False

                # Delete related parts first (due to foreign key constraint)
                session.query(CustomBotParts).filter_by(custom_robot_id=bot_id).delete()

                # Now delete the bot
                session.delete(bot)
                session.commit()
                print(f"Custom bot {bot_id} deleted successfully.")
                return True

            except Exception as e:
                session.rollback()
                print(f"Error deleting bot {bot_id}: {e}")
                return False

    def delete_robot_part(self, part_id: int):
        """
        Delete a robot part if it's not used in any ordered/shipped/cancelled bots.
        Also allows deletion if the part is not used at all.

        Args:
            part_id (int): ID of the robot part to delete.

        Returns:
            bool: True if deletion succeeded, False otherwise.
        """
        with Session(self._engine) as session:
            try:
                part = session.get(RobotParts, part_id)
                if not part:
                    print(f"No robot part found with ID {part_id}")
                    return False

                # Get all custom_robot_ids using this part
                stmt_part_used = select(CustomBotParts.custom_robot_id).where(
                    CustomBotParts.robot_part_id == part_id
                )
                custom_bot_ids = list(session.scalars(stmt_part_used))

                if custom_bot_ids:
                    # Check if any of these bots have been ordered/shipped/cancelled
                    restricted_statuses = {"ordered", "shipped", "cancelled"}
                    stmt_check_orders = select(Order.id).where(
                        and_(
                            Order.custom_robot_id.in_(custom_bot_ids),
                            Order.status.in_(restricted_statuses)
                        )
                    )
                    # if the query has at least one result back
                    # it means that the part is included in at least one order
                    # which has one of the restricted_statuses
                    if session.scalars(stmt_check_orders).first():
                        print("Cannot delete part: It is used in a bot that has been ordered/shipped/cancelled.")
                        return False

                    # Delete part usage from in-progress bots
                    session.query(CustomBotParts).filter(
                        CustomBotParts.robot_part_id == part_id
                    ).delete()

                # Now delete the part itself
                session.delete(part)
                session.commit()
                print(f"Robot part ID {part_id} deleted successfully.")
                return True

            except Exception as e:
                session.rollback()
                print(f"Error deleting robot part: {e}")
                return False

    def delete_part_from_custom_bot(self, bot_id: int, part_id: int):
        """
        Delete a specific part from a custom bot if the bot is still in progress and not ordered.

        Args:
            bot_id (int): ID of the custom bot.
            part_id (int): ID of the robot part to remove.

        Returns:
            bool: True if deletion succeeded, False otherwise.
        """
        with Session(self._engine) as session:
            try:
                # Check if the custom bot exists and is in progress
                custom_bot = session.get(CustomBots, bot_id)
                if not custom_bot:
                    print(f"No custom bot found with ID {bot_id}")
                    return False

                if custom_bot.status != "in_progress":
                    print("Cannot delete part: Bot is not in 'in_progress' state.")
                    return False

                # Check if this bot is referenced in any orders
                order_exists = session.scalars(
                    select(Order.id).where(Order.custom_robot_id == bot_id)
                ).first()
                if order_exists:
                    print("Cannot delete part: Bot is associated with an order.")
                    return False

                # Check if the part exists in this bot
                stmt = select(CustomBotParts).where(
                    and_(
                        CustomBotParts.custom_robot_id == bot_id,
                        CustomBotParts.robot_part_id == part_id
                    )
                )
                bot_part = session.scalars(stmt).first()

                if not bot_part:
                    print("Part not found in this bot.")
                    return False

                # Delete the part from the bot
                session.query(CustomBotParts).filter(
                    CustomBotParts.custom_robot_id == bot_id,
                    CustomBotParts.robot_part_id == part_id
                ).delete()

                session.commit()
                print(f"Part ID {part_id} removed from bot ID {bot_id}.")
                return True

            except Exception as e:
                session.rollback()
                print(f"Error deleting part from bot: {e}")
                return False

    def delete_order(self, order_id: int):
        """
        Delete a pending order and revert its associated custom bot's status to 'in_progress'.

        Args:
            order_id (int): ID of the order to delete.

        Returns:
            bool: True if deletion succeeded, False otherwise.
        """
        with Session(self._engine) as session:
            try:
                # Retrieve the order
                order = session.get(Order, order_id)
                if not order:
                    print(f"No order found with ID {order_id}")
                    return False

                if order.status != "pending":
                    print("Only 'pending' orders can be deleted.")
                    return False

                # Get the associated custom bot
                bot = session.get(CustomBots, order.custom_robot_id)
                if not bot:
                    print("Associated custom bot not found.")
                    return False

                # Delete the order
                session.delete(order)

                # Revert bot status to 'in_progress'
                bot.status = "in_progress"

                session.commit()
                print(f"Order ID {order_id} deleted, custom bot status reverted to 'in_progress'.")
                return True

            except Exception as e:
                session.rollback()
                print(f"Error deleting order: {e}")
                return False


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
'''
print(data_manager.get_parts_from_custom_bot(custom_robot_id=1))
print(data_manager.get_order(custom_robot_id = 1))
print(data_manager.update_bot_part(part_id=1, price=10))
print(data_manager.get_parts_from_custom_bot(custom_robot_id=1))
print(data_manager.get_order(id=1))
data_manager.delete_user(user_id=1)
data_manager.get_order(id=1)
