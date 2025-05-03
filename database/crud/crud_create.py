from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import datetime
from database.database_sql_struct import Users, RobotParts, CustomBots, CustomBotParts, Order


def add_user(engine, users_list):
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

    with Session(engine) as session:
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


def add_part(engine, parts_list):
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
        with Session(engine) as session:
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


def create_custom_bot_for_user(engine, bots_list):
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

    with Session(engine) as session:
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


def add_part_to_custom_bot(engine, part_id, custom_robot_id, amount):
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
    with Session(engine) as session:
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


def add_order(engine, orders_list):
    '''
    Adds a list of orders to the database, each order containing a user ID
    and a custom bot ID. Calculates total price based on bot's price and quantity.
    Also updates the custom bot status to "ordered" once the order is placed.
    '''
    if not orders_list or not isinstance(orders_list, list):
        print("orders_list is empty or not a valid list!")
        return False

    with Session(engine) as session:
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
