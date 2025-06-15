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
    Retrieves robot parts with optional filters, pagination, and exclusion.

    Query parameters:
    - id: int
    - name: str
    - part_type: str
    - price: float
    - page: int (default 1)
    - page_size: int (default 10)
    - exclude_ids: comma-separated list of part IDs to exclude
    """
    id = request.args.get("id", type=int)
    name = request.args.get("name")
    part_type = request.args.get("part_type")
    price = request.args.get("price", type=float)
    page = request.args.get("page", default=1, type=int)
    page_size = request.args.get("page_size", default=10, type=int)
    exclude_ids_raw = request.args.get("exclude_ids")  # e.g. "3,5,7"

    exclude_ids = []
    if exclude_ids_raw:
        exclude_ids = [int(x) for x in exclude_ids_raw.split(",") if x.isdigit()]

    search_criteria = {}
    if id:
        search_criteria["id"] = id
    if name:
        search_criteria["name"] = name
    if part_type:
        search_criteria["type"] = part_type
    if price is not None:
        search_criteria["price"] = price

    result = sql_db.get_part_paginated(page, page_size, exclude_ids, **search_criteria)

    if result is False:
        return jsonify({"error": "Search failed or invalid parameters"}), 400
    else:
        return jsonify(result), 200


@parts_bp.route("/all_part_type_metadata", methods=["GET"])
def get_all_part_type_metadata():
    try:
        result = sql_db.get_all_part_type_metadata()
        print("we are getting all part_type_metadata: ", result)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@parts_bp.route("/metadata", methods=["POST"])
def add_or_update_part_type_metadata():
    data = request.get_json()
    part_type = data.get("type")
    is_asym = data.get("is_asymmetrical")

    try:
        result = sql_db.create_part_type_metadata(part_type, is_asym)
        if result == "exists":
            return jsonify({"message": f"Part type '{part_type}' already registered."}), 200
        elif result == "created":
            return jsonify({"message": f"Part type '{part_type}' created successfully."}), 201
    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# update
@parts_bp.route("/", methods=["PUT"])
def update_part():
    """
    Update one or more attributes of a robot part.

    If its price changes, the database handling function update_bot_part
    will recalculate total_price for orders with 'pending' status
    that include the updated part and make appropriate changes in the database

    Allowed part_type values: {"skeleton","head", "arm", "upper_arm", "lower_arm", "hand", "shoulder", "chest", "upper_waist",
                     "lower_waist", "side_skirt", "front_skirt",
                     "back_skirt",
                     "upper_leg",
                     "lower_leg", "knee", "foot", "backpack"}
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
    allowed_types = {"skeleton", "head", "arm", "upper_arm", "lower_arm", "hand", "shoulder", "chest", "upper_waist",
                     "lower_waist", "side_skirt", "front_skirt",
                     "back_skirt",
                     "upper_leg",
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
