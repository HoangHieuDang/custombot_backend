from sqlalchemy.orm import Session
from sqlalchemy import select
from database.database_sql_struct import Users, RobotParts, CustomBots, CustomBotParts, Order


def get_user(engine, **criteria):
    """
    Fetches users from the database based on provided search criteria.

    Args:
        engine: SQLAlchemy engine for the DB connection.
        **criteria: Filters such as id, email, username, created_at.

    Returns:
        - List of user dictionaries if found.
        - Empty list if no user matches.
        - False if an error or invalid filter is provided.
    """
    possible_filters = {"id", "email", "username", "created_at"}

    if not criteria:
        print("No search criteria provided!")
        return False

    with Session(engine) as session:
        filter_conditions = []

        # Validate and prepare filter conditions
        for attr, value in criteria.items():
            if attr in possible_filters:
                try:
                    column = getattr(Users, attr)
                    filter_conditions.append(column == value)
                except Exception as e:
                    print(f"Error processing filter '{attr}': {e}")
                    return False
            else:
                print(f"Invalid filter key: {attr}")
                return False

        if not filter_conditions:
            print("No valid filters after processing.")
            return False

        try:
            # Execute the query with all filter conditions (AND logic)
            query = select(Users).where(*filter_conditions)
            result = session.scalars(query).all()

            # Return list of user dicts if found, otherwise an empty list
            return [{
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "created_at": user.created_at
            } for user in result] if result else []

        except Exception as e:
            print("Database query failed:", e)
            return False


def get_custom_bot(engine, **criteria):
    """
    Fetches custom bots from the database based on search criteria.

    Args:
        engine: SQLAlchemy engine for DB connection.
        **criteria: Filter keys such as id, user_id, name, status, created_at.

    Returns:
        - List of custom bot dictionaries if found.
        - Empty list if no match.
        - False if invalid filters or DB error occurs.
    """
    possible_filters = {"id", "user_id", "name", "status", "created_at"}

    if not criteria:
        print("No search criteria provided!")
        return False

    with Session(engine) as session:
        filter_conditions = []

        # Validate and prepare filter conditions
        for attr, value in criteria.items():
            if attr in possible_filters:
                try:
                    column = getattr(CustomBots, attr)
                    filter_conditions.append(column == value)
                except Exception as e:
                    print(f"Error processing filter '{attr}': {e}")
                    return False
            else:
                print(f"Invalid filter key: {attr}")
                return False

        if not filter_conditions:
            print("No valid filters after processing.")
            return False

        try:
            # Execute the query with combined AND conditions
            query = select(CustomBots).where(*filter_conditions)
            result = session.scalars(query).all()

            # Return list of bots if found, otherwise empty list
            return [{
                "id": bot.id,
                "user_id": bot.user_id,
                "name": bot.name,
                "status": bot.status,
                "created_at": bot.created_at
            } for bot in result] if result else []

        except Exception as e:
            print("Database query failed:", e)
            return False


def get_part(engine, **criteria):
    """
    Retrieve robot parts matching given filters.

    Args:
        **criteria: Filters like 'id', 'name', 'type', 'price'.

    Returns:
        - List of part dicts if found.
        - Empty list if no match.
        - False if invalid filters or errors.
    """
    possible_filters = {"id", "name", "type", "price"}

    if not criteria:
        print("No search criteria provided!")
        return False

    with Session(engine) as session:
        filter_conditions = []

        # Validate and collect filter conditions
        for attr, value in criteria.items():
            if attr in possible_filters:
                try:
                    column = getattr(RobotParts, attr)
                    filter_conditions.append(column == value)
                except Exception as e:
                    print(f"Error building filter for '{attr}': {e}")
                    return False
            else:
                print(f"Invalid filter key: '{attr}'")
                return False

        if not filter_conditions:
            print("No valid filters applied!")
            return False

        # Combine all filters using AND logic
        combined_filter = filter_conditions.pop(0)
        for condition in filter_conditions:
            combined_filter &= condition

        try:
            query = select(RobotParts).where(combined_filter)
            results = session.scalars(query).all()

            if not results:
                print("No matching parts found.")
                return []

            return [{
                "id": row.id,
                "name": row.name,
                "type": row.type,
                "model_path": row.model_path,
                "img_path": row.img_path,
                "price": row.price
            } for row in results]

        except Exception as e:
            print(f"Query failed: {e}")
            return False


def get_order(engine, **criteria):
    """
    Retrieve orders matching given filters.

    Args:
        **criteria: Filters like 'id', 'user_id', 'status', etc.

    Returns:
        - List of order dicts if found.
        - Empty list if no match.
        - False if invalid filters or query error.
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

        # Build filter conditions based on valid keys
        for attr, value in criteria.items():
            if attr in possible_filters:
                try:
                    column = getattr(Order, attr)
                    filter_conditions.append(column == value)
                except Exception as e:
                    print(f"Error processing filter '{attr}': {e}")
                    return False
            else:
                print(f"Invalid filter key: '{attr}'")
                return False

        if not filter_conditions:
            print("No valid filters applied!")
            return False

        # Combine filters with AND logic
        combined_filter = filter_conditions.pop(0)
        for condition in filter_conditions:
            combined_filter &= condition

        try:
            query = select(Order).where(combined_filter)
            results = session.scalars(query).all()

            if not results:
                print("No matching orders found.")
                return []

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
            } for row in results]

        except Exception as e:
            print(f"Query failed: {e}")
            return False


def get_parts_from_custom_bot(engine, custom_robot_id):
    """
    Retrieve all parts linked to a given custom robot.

    Args:
        custom_robot_id (int): ID of the custom robot.

    Returns:
        - List of part dicts if found.
        - Empty list if no parts are linked.
        - False if ID is invalid or query fails.
    """
    if not isinstance(custom_robot_id, int):
        print("Invalid custom_robot_id!")
        return False

    with Session(engine) as session:
        try:
            # First check if the custom robot exists
            exists_query = select(CustomBots).where(CustomBots.id == custom_robot_id)
            bot = session.scalar(exists_query)

            if not bot:
                print(f"Custom robot with ID {custom_robot_id} does not exist.")
                return False

            # Proceed to fetch the parts
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

            results = session.execute(query).all()

            if not results:
                print("No parts found for this custom robot.")
                return []

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
            } for row in results]

        except Exception as e:
            print(f"Query failed: {e}")
            return False

