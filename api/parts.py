from flask import Blueprint, request, jsonify
from database import database_handling as db

parts_bp = Blueprint("parts", __name__)
sql_db = db.SQLiteDataManager("./database/custom_bot_db")


# create
@parts_bp.route("/", methods=["POST"])
def create_part():
    # Extract data from JSON request body
    data = request.get_json()
    name = data.get("name")
    part_type = data.get("type")
    model_path = data.get("model_path")
    img_path = data.get("img_path")
    price = data.get("price")

    # Validate required fields
    if not all([name, part_type, model_path, img_path, price]):
        return jsonify({"error": "Missing required fields"}), 400

    # Prepare part data as a list of dicts
    new_part = [{
        "name": name,
        "type": part_type,
        "model_path": model_path,
        "img_path": img_path,
        "price": price
    }]

    # Attempt to insert the part into the database
    result = sql_db.add_part(new_part)
    if result:
        return jsonify({"message": f"Part '{name}' created successfully"}), 201
    else:
        return jsonify({"error": "Database failed to create part"}), 400


# read
@parts_bp.route("/", methods=["GET"])
def get_part():
    """
    Retrieves a part from the database based on dynamic search criteria.

    Acceptable query parameters:
        - id: The unique identifier of the part.
        - name: The name of the part.
        - part_type: The type/category of the part.
        - price: The price of the part.
    """
    id = request.args.get("id", type=int)
    name = request.args.get("name")
    part_type = request.args.get("part_type")
    price = request.args.get("price", type=float)

    search_criteria = {}
    if id:
        search_criteria["id"] = id
    if name:
        search_criteria["name"] = name
    if part_type:
        search_criteria["type"] = part_type
    if price is not None:
        search_criteria["price"] = price

    result = sql_db.get_part(**search_criteria)

    if result is False:
        return jsonify({"error": "Search failed or invalid parameters"}), 400
    else:
        return jsonify(result), 200


# update
@parts_bp.route("/", methods=["PUT"])
def update_part():
    """
    Update one or more attributes of a robot part.

    If its price changes, the database handling function update_bot_part
    will recalculate total_price for orders with 'pending' status
    that include the updated part and make appropriate changes in the database

    Allowed part_type values: {"arm", "shoulder", "chest", "skirt", "leg", "foot", "backpack"}
    Updatable fields: {"name", "type", "model_path", "img_path", "price"}

    Expected JSON:
    {
        "id": int,
        "name": str (optional),
        "part_type": str (optional),
        "model_path": str (optional),
        "img_path": str (optional),
        "price": float (optional)
    }
    """
    data = request.get_json()
    part_id = data.get("id")

    if not part_id:
        return jsonify({"error": "Missing required field 'id'"}), 400

    allowed_types = {"arm", "upper_arm", "lower_arm", "hand", "shoulder", "chest", "waist", "skirt", "upper_leg",
                     "lower_leg", "knee", "foot", "backpack"}

    update_fields = {}

    # Map "part_type" to "type" (column name)
    part_type = data.get("part_type")
    if part_type:
        if part_type not in allowed_types:
            return jsonify({"error": f"Invalid part_type '{part_type}'. Allowed: {allowed_types}"}), 400
        update_fields["type"] = part_type

    # Collect other fields if present
    for field in ["name", "model_path", "img_path", "price"]:
        if field in data:
            update_fields[field] = data[field]

    if not update_fields:
        return jsonify({"error": "No valid fields provided to update."}), 400

    result = sql_db.update_bot_part(part_id, **update_fields)

    if result:
        return jsonify({"message": f"Part {part_id} updated successfully."}), 200
    else:
        return jsonify({"error": f"Failed to update part {part_id}."}), 400


# delete
@parts_bp.route("/<int:part_id>", methods=["DELETE"])
def delete_robot_part(part_id):
    success = sql_db.delete_robot_part(part_id)
    if success:
        return jsonify({"message": f"Part {part_id} deleted"}), 204
    else:
        return jsonify({"error": f"Can not delete part {part_id}"}), 400
