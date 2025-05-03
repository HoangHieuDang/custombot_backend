from sqlalchemy.orm import Session
from sqlalchemy import select
from database.database_sql_struct import Users, RobotParts, CustomBots, CustomBotParts, Order


def get_user(engine, **criteria):
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

    with Session(engine) as session:
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


def get_custom_bot(engine, **criteria):
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

    with Session(engine) as session:
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


def get_part(engine, **criteria):
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

    with Session(engine) as session:
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


def get_order(engine, **criteria):
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

    with Session(engine) as session:
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


def get_parts_from_custom_bot(engine, custom_robot_id):
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
    with Session(engine) as session:
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
