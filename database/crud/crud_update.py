from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from database.database_sql_struct import Users, RobotParts, CustomBots, CustomBotParts, Order, PartTypeMetadata
from sqlalchemy.exc import SQLAlchemyError
from api.extensions import bcrypt


def update_user(engine, user_id, **changes):
    allowed_fields = {"email", "username", "password"}
    with Session(engine) as session:
        try:
            user = session.scalar(select(Users).where(Users.id == user_id))
            if not user:
                return {"success": False, "error": f"User {user_id} not found."}

            for key, value in changes.items():
                if key not in allowed_fields:
                    return {"success": False, "error": f"Invalid field '{key}'."}

                # Uniqueness checks
                if key == "username":
                    conflict = session.scalar(select(Users).where(Users.username == value, Users.id != user_id))
                    if conflict:
                        return {"success": False, "error": "Username already taken."}
                if key == "email":
                    conflict = session.scalar(select(Users).where(Users.email == value, Users.id != user_id))
                    if conflict:
                        return {"success": False, "error": "Email already in use."}
                if key == "password":
                    value = bcrypt.generate_password_hash(value).decode("utf-8")

                setattr(user, key, value)

            session.commit()
            return {"success": True}
        except Exception as e:
            print(f"Error updating user {user_id}: {e}")
            return {"success": False, "error": "Database error during update."}


def update_custom_bot(engine, bot_id, **changes):
    """
    Updates the non-critical attributes of a custom robot in the database.

    Args:
        bot_id (int): The unique identifier of the custom robot to update.
        **changes (dict): Key-value pairs representing the fields to update.
                          Only the 'name' field is allowed.

    Returns:
        tuple:
            - success (bool): True if the update was successful, False otherwise.
            - message (str): Description of what happened or went wrong.
    """
    allowed_changes = {"name"}

    with Session(engine) as session:
        for key, value in changes.items():
            if key not in allowed_changes:
                return False, f"Invalid update field '{key}' — only 'name' is allowed."

            try:
                custom_bot = session.execute(
                    select(CustomBots).filter_by(id=bot_id)
                ).scalar_one_or_none()

                if not custom_bot:
                    return False, f"Custom bot with id {bot_id} not found."

                if key == "name":
                    name_conflict = session.execute(
                        select(CustomBots).where(
                            and_(
                                CustomBots.user_id == custom_bot.user_id,
                                CustomBots.name == value,
                                CustomBots.id != bot_id
                            )
                        )
                    ).first()

                    if name_conflict:
                        return False, f"Bot name '{value}' already exists for user {custom_bot.user_id}."

                setattr(custom_bot, key, value)
                session.commit()
                return True, f"Custom bot {bot_id} updated successfully."

            except SQLAlchemyError as e:
                session.rollback()
                return False, f"Database error: {str(e)}"


def update_bot_part(engine, part_id, **changes):
    '''
    Update one or more attributes of a robot part. If its price changes,
    recalculate total_price for orders with 'pending' status that include the updated part.
    '''
    allowed_types = {"skeleton", "head", "arm", "upper_arm", "lower_arm", "hand", "shoulder", "chest", "upper_waist",
                     "lower_waist", "side_skirt", "front_skirt",
                     "back_skirt",
                     "upper_leg",
                     "lower_leg", "knee", "foot", "backpack"}
    possible_changes = {"name", "type", "model_path", "img_path", "price"}
    with Session(engine) as session:
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
                    with Session(engine) as revert_session:
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


def update_order(engine, order_id, **changes):
    """
    Update attributes of an existing order.
    Automatically recalculates total_price based on updated quantity.

    Returns:
        bool: True if update succeeded, False otherwise.
    """
    from sqlalchemy import select
    from datetime import datetime, date

    possible_status = {"pending", "paid", "production", "shipping", "received", "cancelled"}
    possible_changes = {"quantity", "status", "shipping_address", "shipping_date", "payment_method"}

    with Session(engine) as session:
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
                    order.quantity = value  # apply quantity first

                elif key == "status":
                    if value not in possible_status:
                        print(f"Invalid status '{value}'. Allowed: {possible_status}")
                        return False
                    order.status = value

                elif key == "shipping_date":
                    if isinstance(value, str):
                        try:
                            value = datetime.strptime(value, "%Y-%m-%d").date()
                        except ValueError:
                            print("shipping_date must be in 'YYYY-MM-DD' format.")
                            return False
                    elif not isinstance(value, date):
                        print("shipping_date must be a string or a date object.")
                        return False
                    order.shipping_date = value

                elif key == "shipping_address":
                    order.shipping_address = value

                elif key == "payment_method":
                    order.payment_method = value

            # Recalculate total_price based on latest quantity
            # Get custom bot price by summing up its parts
            if "quantity" in changes:
                parts_query = (
                    select(RobotParts.price, CustomBotParts.robot_part_amount)
                    .join(CustomBotParts, RobotParts.id == CustomBotParts.robot_part_id)
                    .where(CustomBotParts.custom_robot_id == order.custom_robot_id)
                )
                part_rows = session.execute(parts_query).all()
                custom_bot_price = sum(p.price * p.robot_part_amount for p in part_rows)

                # Finally update total_price
                order.total_price = order.quantity * custom_bot_price

            session.commit()
            print(f"Order {order_id} updated successfully.")
            return True

        except Exception as e:
            session.rollback()
            print(f"Error updating order {order_id}: {e}")
            return False


def update_part_on_custom_bot(engine, custom_robot_id, new_part_id, direction, amount=1):
    """
    Updates the custom bot to use a new robot part in a given direction ('left', 'right', 'center').

    If a part already exists for that direction and type, it will be replaced.

    Args:
        engine: SQLAlchemy engine.
        custom_robot_id (int): The ID of the custom bot.
        new_part_id (int): The ID of the new robot part to assign.
        direction (str): One of 'left', 'right', 'center'.
        amount (int): Quantity to assign (default is 1).

    Returns:
        bool: True if updated successfully, False otherwise.
    """
    if direction not in ("left", "right", "center"):
        print("Invalid direction!")
        return False

    if amount < 1:
        print("Amount must be >= 1.")
        return False

    with Session(engine) as session:
        try:
            # Validate bot
            bot = session.scalar(select(CustomBots).where(CustomBots.id == custom_robot_id))
            if not bot:
                print(f"Bot ID {custom_robot_id} not found.")
                return False
            if bot.status == "ordered":
                print(f"Bot '{bot.name}' already ordered — cannot update.")
                return False

            # Validate part
            new_part = session.scalar(select(RobotParts).where(RobotParts.id == new_part_id))
            if not new_part:
                print(f"No robot part found with ID {new_part_id}.")
                return False

            # Remove any existing part of same type & direction
            existing_entry = session.scalar(
                select(CustomBotParts)
                .join(RobotParts, CustomBotParts.robot_part_id == RobotParts.id)
                .where(
                    CustomBotParts.custom_robot_id == custom_robot_id,
                    CustomBotParts.direction == direction,
                    RobotParts.type == new_part.type
                )
            )

            if existing_entry:
                session.delete(existing_entry)
                session.flush()  # Safe to remove before re-adding

            # Add new part
            new_custom_part = CustomBotParts(
                custom_robot_id=custom_robot_id,
                robot_part_id=new_part_id,
                direction=direction,
                robot_part_amount=amount
            )
            session.add(new_custom_part)

            session.commit()
            print(f"Updated bot {custom_robot_id} with part {new_part_id} at direction {direction}.")
            return True

        except Exception as e:
            session.rollback()
            print(f"Failed to update part: {e}")
            return False
