from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from database.database_sql_struct import Users, RobotParts, CustomBots, CustomBotParts, Order


def update_user(engine, user_id, **changes):
    """
        Updates user attributes in the database based on the provided changes.

        Args:
            user_id (int): The unique identifier of the user to update.
            **changes (dict): A variable-length dictionary of key-value pairs representing
                              the attributes to update and their new values. Only the following
                              keys are allowed:
                                - 'email': The new email address.
                                - 'username': The new username.
                                - 'password': The new password

        Returns:
            bool:
                - True if the update was successful.
                - False if an invalid attribute is provided or if an error occurs during the update.

        Raises:
            Exception: Any exceptions raised during the database transaction are caught and
                       printed to help with debugging.

        Example:
            update_user(1, email="new@example.com", username="new_name", password="dffdfd")

        Notes:
            - The function uses SQLAlchemy ORM to query and update the user.
            - Only the fields explicitly listed in `possible_changes` can be updated.
            - The update is committed to the database only if all inputs are valid.
        """
    possible_changes = {"email", "username", "password"}
    with Session(engine) as session:
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


def update_custom_bot(engine, bot_id, **changes):
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
    with Session(engine) as session:
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
