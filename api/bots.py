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

    if user_id and name:
        success = sql_db.create_custom_bot_for_user([{"user_id": user_id, "name": name}])
        if success:
            return jsonify({"message": f"Custom Bot '{name}' created successfully for user_id {user_id}"}), 201
        else:
            return jsonify({"error": "Database couldn't create the new custom bot"}), 400
    else:
        return jsonify({"error": "Can not create custom bot! Missing required fields"}), 400


@bots_bp.route("/add_part_to_bot", methods=["POST"])
def add_part_to_bot():
    data = request.get_json()
    part_id = data.get("part_id")
    custom_robot_id = data.get("custom_robot_id")
    amount = data.get("amount")

    if part_id and custom_robot_id and amount:
        success = sql_db.add_part_to_custom_bot(part_id, custom_robot_id, amount)
        if success:
            return jsonify(
                {"message": f"{amount} of parts {part_id} added successfully to custom bot {custom_robot_id}!"}), 201
        else:
            return jsonify({"error": f"can't add part {part_id} to custom bot {custom_robot_id}"}), 400


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


# Delete
@bots_bp.route("/<int:bot_id>/<int:part_id>", methods=["DELETE"])
def delete_part_from_custom_bot(bot_id, part_id):
    success = sql_db.delete_part_from_custom_bot(bot_id, part_id)
    if success:
        return jsonify({"message": f"Part {part_id} deleted from custom bot {bot_id}"}), 204
    else:
        return jsonify({"error": f"Can not delete part {part_id} from custom bot {bot_id}"}), 400
