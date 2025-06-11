from flask import Blueprint, request, jsonify
from database import database_handling as db

bots_bp = Blueprint("custom_bots", __name__)
sql_db = db.SQLiteDataManager("./database/custom_bot_db")


# Create
@bots_bp.route("/add_custom_bot", methods=["POST"])
def create_custom_bot():
    data = request.get_json()
    user_id = data.get("user_id")
    name = data.get("name")

    if not user_id or not name:
        return jsonify({"error": "Missing required fields: 'user_id' and 'name'"}), 400

    success, message = sql_db.create_custom_bot_for_user([{"user_id": user_id, "name": name}])

    if success:
        return jsonify({"message": message}), 201
    else:
        return jsonify({"error": message}), 400


@bots_bp.route("/add_part_to_bot", methods=["POST"])
def add_part_to_bot():
    data = request.get_json()

    part_id = data.get("part_id")
    custom_robot_id = data.get("custom_robot_id")
    amount = data.get("amount")
    direction = data.get("direction")

    # Basic validation
    if not all([part_id, custom_robot_id, amount, direction]):
        return jsonify({"error": "Missing required fields: part_id, custom_robot_id, amount, direction"}), 400

    if direction not in ("left", "right", "center"):
        return jsonify({"error": "Invalid direction. Must be 'left', 'right', or 'center'"}), 400

    # Call the updated DB function
    success = sql_db.add_part_to_custom_bot(
        part_id=part_id,
        custom_robot_id=custom_robot_id,
        amount=amount,
        direction=direction
    )

    if success:
        return jsonify({
            "message": f"{amount} of part {part_id} added successfully to bot {custom_robot_id} ({direction})!"
        }), 201
    else:
        return jsonify({
            "error": f"Unable to add part {part_id} to bot {custom_robot_id} in direction {direction}."
        }), 400


# Read

@bots_bp.route("/bots", methods=["GET"])
def get_custom_bot():
    id = request.args.get("id", type=int)
    user_id = request.args.get("user_id", type=int)
    name = request.args.get("name")
    status = request.args.get("status")
    created_at = request.args.get("created_at")

    search_fields = {}
    if id:
        search_fields["id"] = id
    if user_id:
        search_fields["user_id"] = user_id
    if name:
        search_fields["name"] = name
    if status:
        if status in ("in_progress", "ordered"):
            search_fields["status"] = status
        else:
            return jsonify({"error": "status must be 'in_progress' or 'ordered'"}), 400
    if created_at:
        search_fields["created_at"] = created_at

    result = sql_db.get_custom_bot(**search_fields)

    if result is False:
        return jsonify({"error": "Invalid search parameters or query error."}), 400
    return jsonify(result), 200


@bots_bp.route("/<int:bot_id>/parts", methods=["GET"])
def get_parts_from_custom_bot(bot_id):
    result = sql_db.get_parts_from_custom_bot(bot_id)

    if result is False:
        return jsonify({"error": f"No parts found or invalid bot ID {bot_id}"}), 400
    return jsonify(result), 200


# Update
@bots_bp.route("/<int:bot_id>", methods=["PUT"])
def update_custom_bot(bot_id):
    updated_data = request.get_json()
    new_name = updated_data.get("name")

    updated_fields = {}
    if new_name:
        updated_fields["name"] = new_name

    if not updated_fields:
        return jsonify({"error": "No update fields provided"}), 400

    update_result = sql_db.update_custom_bot(bot_id, **updated_fields)
    if update_result:
        return jsonify({"message": f"Custom Bot {bot_id} updated"}), 200
    else:
        return jsonify({"error": f"Cannot update Custom Bot {bot_id}"}), 400


@bots_bp.route("/<int:bot_id>/update_part", methods=["PUT"])
def update_part_on_custom_bot(bot_id):
    data = request.get_json()

    new_part_id = data.get("part_id")
    direction = data.get("direction")
    amount = data.get("amount", 1)  # default to 1 if not provided

    if not all([new_part_id, direction]):
        return jsonify({"error": "Missing required fields: part_id and direction"}), 400

    if direction not in ("left", "right", "center"):
        return jsonify({"error": "Invalid direction. Must be 'left', 'right', or 'center'"}), 400

    success = sql_db.update_part_on_custom_bot(
        custom_robot_id=bot_id,
        new_part_id=new_part_id,
        direction=direction,
        amount=amount
    )

    if success:
        return jsonify({
            "message": f"Part {new_part_id} updated in bot {bot_id} at {direction}."
        }), 200
    else:
        return jsonify({
            "error": f"Failed to update part in bot {bot_id} at {direction}."
        }), 400


# Delete
@bots_bp.route("/<int:bot_id>/<int:part_id>", methods=["DELETE"])
def delete_part_from_custom_bot(bot_id, part_id):
    direction = request.args.get("direction")

    if not direction or direction not in ("left", "right", "center"):
        return jsonify({"error": "Missing or invalid 'direction'. Must be 'left', 'right', or 'center'."}), 400

    success = sql_db.delete_part_from_custom_bot(bot_id, part_id, direction)

    if success:
        return jsonify({
            "message": f"Part {part_id} ({direction}) deleted from custom bot {bot_id}"
        }), 204
    else:
        return jsonify({
            "error": f"Cannot delete part {part_id} ({direction}) from custom bot {bot_id}"
        }), 400
