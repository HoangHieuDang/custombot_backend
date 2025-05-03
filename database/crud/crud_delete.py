from sqlalchemy.orm import Session
from sqlalchemy import select, and_, delete
from database.database_sql_struct import Users, RobotParts, CustomBots, CustomBotParts, Order


def delete_user(engine, user_id):
    """
    Delete a user and their related data, while preserving legal Order records.

    Orders with status 'paid', 'shipped', or 'cancelled' will be retained,
    and their user_id will be set to None for anonymization.

    Args:
        user_id (int): ID of the user to delete.

    Returns:
        bool: True if user deleted successfully, False otherwise.
    """
    with Session(engine) as session:
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


def delete_custom_bot_from_user(engine, user_id, bot_id):
    """
    Delete a custom bot belonging to a user, only if it is still in 'in_progress' status.

    Args:
        user_id (int): ID of the user.
        bot_id (int): ID of the custom bot.

    Returns:
        bool: True if the deletion was successful, False otherwise.
    """
    with Session(engine) as session:
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


def delete_robot_part(engine, part_id: int):
    """
    Delete a robot part if it's not used in any ordered/shipped/cancelled bots.
    Also allows deletion if the part is not used at all.

    Args:
        part_id (int): ID of the robot part to delete.

    Returns:
        bool: True if deletion succeeded, False otherwise.
    """
    with Session(engine) as session:
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


def delete_part_from_custom_bot(engine, bot_id: int, part_id: int):
    """
    Delete a specific part from a custom bot if the bot is still in progress and not ordered.

    Args:
        bot_id (int): ID of the custom bot.
        part_id (int): ID of the robot part to remove.

    Returns:
        bool: True if deletion succeeded, False otherwise.
    """
    with Session(engine) as session:
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


def delete_order(engine, order_id: int):
    """
    Delete a pending order and revert its associated custom bot's status to 'in_progress'.

    Args:
        order_id (int): ID of the order to delete.

    Returns:
        bool: True if deletion succeeded, False otherwise.
    """
    with Session(engine) as session:
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
