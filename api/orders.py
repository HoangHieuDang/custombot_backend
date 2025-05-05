from flask import Blueprint, request, jsonify
from database import database_handling as db

orders_bp = Blueprint("orders", __name__)
sql_db = db.SQLiteDataManager("./database/custom_bot_db")


# Create
@orders_bp.route("/", methods=['POST'])
def add_order():
    allowed_status = ("pending", "paid", "shipped", "cancelled")
    order = request.get_json()

    try:
        user_id = int(order.get("user_id"))
        custom_robot_id = int(order.get("custom_robot_id"))
        quantity = float(order.get("quantity"))
        status = order.get("status")
        payment_method = order.get("payment_method")
        shipping_address = order.get("shipping_address")
        shipping_date = order.get("shipping_date")  # string or ISO datetime
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid type for one or more fields"}), 400

    if not all([user_id, custom_robot_id, quantity, status, payment_method, shipping_address, shipping_date]):
        return jsonify({"error": "Missing required fields"}), 400

    if status not in allowed_status:
        return jsonify({"error": f"status only accepts the following values: {allowed_status}"}), 400

    new_order = [{
        "user_id": user_id,
        "custom_robot_id": custom_robot_id,
        "quantity": quantity,
        "status": status,
        "payment_method": payment_method,
        "shipping_address": shipping_address,
        "shipping_date": shipping_date
    }]

    result = sql_db.add_order(new_order)
    if result:
        return jsonify({"message": f"Order for user {user_id} created successfully"}), 201
    else:
        return jsonify({"error": "Database failed to create order"}), 400


# Read
@orders_bp.route("/", methods=["GET"])
def get_order():
    '''
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
    :return:
    '''
    id = request.args.get("id", type=int)
    user_id = request.args.get("user_id", type=int)
    custom_robot_id = request.args.get("custom_robot_id", type=int)
    quantity = request.args.get("quantity", type=int)
    total_price = request.args.get("total_price", type=float)
    status = request.args.get("status")
    payment_method = request.args.get("payment_method")
    shipping_address = request.args.get("shipping_address")
    shipping_date = request.args.get("shipping_date")
    created_at = request.args.get("created_at")

    search_fields = {}
    if id:
        search_fields["id"] = id
    if user_id:
        search_fields["user_id"] = user_id
    if custom_robot_id:
        search_fields["custom_robot_id"] = custom_robot_id
    if quantity:
        search_fields["quantity"] = quantity
    if total_price:
        search_fields["total_price"] = total_price
    allowed_statuses = {"pending", "paid", "shipped", "cancelled"}
    if status:
        if status not in allowed_statuses:
            return jsonify({"error": f"Invalid status '{status}'. Allowed: {allowed_statuses}"}), 400
        else:
            search_fields["status"] = status
    if payment_method:
        search_fields["payment_method"] = payment_method
    if shipping_address:
        search_fields["shipping_address"] = shipping_address
    if shipping_date:
        search_fields["shipping_date"] = shipping_date
    if created_at:
        search_fields["created_at"] = created_at

    if not search_fields:
        return jsonify({"error": "No search criterias provided"}), 400
    else:
        result = sql_db.get_order(**search_fields)
        if result is False:
            return jsonify({"error": "Search failed or invalid parameters"}), 400
        elif not result:
            return jsonify([]), 200  # Return empty list if nothing found
        else:
            return jsonify(result), 200


# Update
@orders_bp.route("/", methods=["PUT"])
def update_order():
    data = request.get_json()
    # get order_id
    order_id = data.get("id")

    if not order_id:
        return jsonify({"error": "Missing order ID"}), 400

    possible_status = {"pending", "paid", "shipped", "cancelled"}
    possible_changes = {"quantity", "status", "shipping_address", "shipping_date", "payment_method"}

    changes = {}

    # check if each key in possible_changes exists in the request
    for key in possible_changes:
        value = data.get(key)
        if value is not None:
            # status only can be one of the possible_status
            if key == "status":
                value = value.strip().lower()
                if value not in possible_status:
                    return jsonify({"error": f"Invalid status '{value}'. Allowed: {possible_status}"}), 400
            # check if quantity > 0 and int
            elif key == "quantity":
                try:
                    value = int(value)
                    if value <= 0:
                        return jsonify({"error": "Quantity must be a positive integer"}), 400
                except ValueError:
                    return jsonify({"error": "Quantity must be an integer"}), 400
            changes[key] = value

    if not changes:
        return jsonify({"error": "No valid fields provided to update"}), 400

    result = sql_db.update_order(order_id, **changes)

    if result:
        return jsonify({"message": f"Order {order_id} updated successfully"}), 200
    else:
        return jsonify({"error": f"Failed to update Order {order_id}"}), 400


# Delete
@orders_bp.route("/<int:order_id>", methods=["DELETE"])
def delete_order(order_id):
    """
    Deletes an order by its ID.

    Args:
        order_id (int): The ID of the order to delete.

    Returns:
        JSON response indicating success or failure.
    """
    success = sql_db.delete_order(order_id)
    if success:
        return jsonify({"message": f"Order {order_id} deleted"}), 204
    else:
        return jsonify({"error": f"Can not delete order {order_id}"}), 400
