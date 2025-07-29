from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, func, and_, or_
from datetime import datetime
from database.database_sql_struct import Users, RobotParts, CustomBots, CustomBotParts, Order, PartTypeMetadata


def add_user(engine, user):
    if not isinstance(user, dict):
        return False, {
            "code": "invalid_format",
            "message": "User data must be a dictionary."
        }

    required_fields = ("username", "email", "password")
    missing = [k for k in required_fields if not user.get(k)]
    if missing:
        return False, {
            "code": "missing_fields",
            "message": f"Missing required fields: {', '.join(missing)}."
        }

    try:
        with Session(engine) as session:
            existing_user = session.execute(
                select(Users).where(
                    or_(
                        Users.username == user["username"],
                        Users.email == user["email"].strip().lower()
                    )
                )
            ).scalar_one_or_none()

            if existing_user:
                return False, {
                    "code": "duplicate_user",
                    "message": "Username or email already exists."
                }

            new_user = Users(
                username=user["username"],
                email=user["email"].strip().lower(),
                password=user["password"],
                created_at=datetime.now()
            )

            session.add(new_user)
            session.commit()

            return True, "User added successfully."

    except SQLAlchemyError as e:
        return False, {
            "code": "db_error",
            "message": f"Database error: {str(e)}"
        }


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
                    # For each new part in parts_list, update the part type and direction type into part type metadata
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
        tuple: (success, message)
            - success (bool): True if at least one bot was successfully added, False otherwise.
            - message (str): Detailed outcome or error message.
    '''
    if not bots_list or not isinstance(bots_list, list):
        return False, "Empty bots_list or invalid data format."

    with Session(engine) as session:
        new_bots_list = []

        for bot in bots_list:
            if not all(k in bot for k in ("user_id", "name")):
                continue  # Skip bots with missing data

            # Check if user exists
            user = session.scalar(select(Users).where(Users.id == bot["user_id"]))
            if not user:
                continue

            # Check if bot name already exists for this user
            existing_bot = session.scalar(
                select(CustomBots).where(
                    and_(
                        CustomBots.user_id == bot["user_id"],
                        CustomBots.name == bot["name"]
                    )
                )
            )
            if existing_bot:
                return False, f"Bot name '{bot['name']}' already exists for user_id {bot['user_id']}"

            try:
                new_bot = CustomBots(
                    user_id=bot["user_id"],
                    name=bot["name"],
                    status="in_progress",
                    created_at=datetime.now(),
                )
                new_bots_list.append(new_bot)
            except Exception as e:
                return False, f"Error creating CustomBot object: {e}"

        if new_bots_list:
            try:
                session.add_all(new_bots_list)
                session.commit()
                return True, f"Successfully added {len(new_bots_list)} custom bot(s)."
            except Exception as e:
                session.rollback()
                return False, f"Database commit failed: {e}"
        else:
            return False, "No valid bots to add."


def add_part_to_custom_bot(engine, part_id, custom_robot_id, amount, direction):
    """

    Args:
        engine:
        part_id:
        custom_robot_id:
        amount:
        direction:

    Returns:

    """
    # Validate direction
    if direction not in ("left", "right", "center"):
        print("Invalid direction. Must be 'left', 'right', or 'center'.")
        return False

    with Session(engine) as session:
        # Validate amount
        if not isinstance(amount, int) or amount < 1:
            print("Amount must be a positive integer >= 1.")
            return False

        # Validate part and part metadata
        part = session.scalar(select(RobotParts).where(RobotParts.id == part_id))
        if not part:
            print(f"No part found with part_id {part_id}.")
            return False

        # Validate part type metadata exists, if not yet registered, the part type should be added there first
        metadata = session.get(PartTypeMetadata, part.type)
        if not metadata:
            print(f"Part type '{part.type}' not registered in PartTypeMetadata. Please add it first.")
            return False

        # Enforce direction consistency with PartTypeMetadata
        if metadata.is_asymmetrical:
            if direction not in ("left", "right"):
                print(f"Invalid direction '{direction}' for asymmetrical part type '{part.type}'.")
                return False
        else:
            if direction != "center":
                print(f"Invalid direction '{direction}' for symmetrical part type '{part.type}'.")
                return False

        # Validate bot
        bot = session.scalar(select(CustomBots).where(CustomBots.id == custom_robot_id))
        if not bot:
            print(f"No custom bot found with id {custom_robot_id}.")
            return False

        if bot.status == "ordered":
            print(f"Cannot modify bot '{bot.name}' (ID {custom_robot_id}) because it has already been ordered.")
            return False

        try:
            # Update or insert part to bot
            existing_entry = session.scalar(
                select(CustomBotParts).where(
                    CustomBotParts.robot_part_id == part_id,
                    CustomBotParts.custom_robot_id == custom_robot_id,
                    CustomBotParts.direction == direction
                )
            )

            if existing_entry:
                existing_entry.robot_part_amount += amount
                print(f"Updated part amount for part_id {part_id} ({direction}) in bot_id {custom_robot_id}.")
            else:
                session.add(CustomBotParts(
                    robot_part_id=part_id,
                    custom_robot_id=custom_robot_id,
                    robot_part_amount=amount,
                    direction=direction
                ))
                print(f"Added part_id {part_id} ({direction}) to bot_id {custom_robot_id}.")

            # Ensure part_type metadata is up-to-date
            part_type = part.type
            metadata_entry = session.scalar(select(PartTypeMetadata).where(PartTypeMetadata.type == part_type))

            if not metadata_entry:
                # Insert new metadata entry
                session.add(PartTypeMetadata(
                    type=part_type,
                    is_asymmetrical=(direction in ("left", "right"))
                ))
                print(f"Inserted new metadata for type '{part_type}' (asym={direction in ('left', 'right')}).")
            else:
                if not metadata_entry.is_asymmetrical and direction in ("left", "right"):
                    metadata_entry.is_asymmetrical = True
                    print(f"Updated metadata for type '{part_type}' to is_asymmetrical=True.")

            session.commit()
            return True

        except Exception as e:
            session.rollback()
            print(f"Failed to add part to custom bot: {e}")
            return False


def create_part_type_metadata(engine, part_type, is_asym):
    if part_type is None or is_asym is None:
        raise ValueError("Both 'part_type' and 'is_asym' must be provided.")
    if not isinstance(is_asym, bool):
        raise TypeError("'is_asym' must be a boolean.")

    with Session(engine) as session:
        existing = session.get(PartTypeMetadata, part_type)
        if existing:
            if existing.is_asymmetrical != is_asym:
                raise ValueError(
                    f"Part type '{part_type}' already exists with is_asymmetrical={existing.is_asymmetrical}. Cannot overwrite.")
            return "exists"
        else:
            session.add(PartTypeMetadata(type=part_type, is_asymmetrical=is_asym))
            session.commit()
            return "created"


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

                # Check if a pending order for this user and bot already exists
                existing_order = session.scalar(
                    select(Order).where(
                        Order.user_id == order['user_id'],
                        Order.custom_robot_id == order['custom_robot_id'],
                        Order.status == "pending"
                    )
                )

                if existing_order:
                    # Update the existing order
                    existing_order.quantity += quantity
                    existing_order.total_price += total_price
                    existing_order.created_at = datetime.now()
                    print(f"[Info] Updated existing pending order with ID {existing_order.id}")
                else:
                    # Create a new order
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

                # Mark bot as ordered
                bot.status = "ordered"
                session.commit()
                print(f"[Success] Order handled for bot ID {bot.id}.")

            except Exception as e:
                print(f"[Error] Failed to add order: {e}")
                session.rollback()
                continue

    return True
