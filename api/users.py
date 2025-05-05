from flask import Blueprint, request, jsonify
from database import database_handling as db

users_bp = Blueprint("users", __name__)
sql_db = db.SQLiteDataManager("./database/custom_bot_db")


# create
@users_bp.route("/", methods=["POST"])
def create_user():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    if username and password and email:
        new_user = [{
            "username": username,
            "email": email,
            "password": password
        }]
        success = sql_db.add_user(new_user)
        if success:
            return jsonify({"message": "User created successfully."}), 201
        else:
            return jsonify({"error": "User creation failed."}), 400
    else:
        return jsonify({"error": "Missing required fields."}), 400


# read
@users_bp.route("/", methods=["GET"])
def get_user():
    id = request.args.get("id", type=int)
    email = request.args.get("email")
    username = request.args.get("username")
    created_at = request.args.get("created_at")

    search_fields = {}
    if id:
        search_fields["id"] = id
    if email:
        search_fields["email"] = email
    if username:
        search_fields["username"] = username
    if created_at:
        search_fields["created_at"] = created_at  # assumed to be a valid string format

    result = sql_db.get_user(**search_fields)

    if result is False:
        return jsonify({"error": "Invalid search parameters or query error."}), 400
    return jsonify(result), 200


# update
@users_bp.route("/<user_id>", methods=["PUT"])
def update_user(user_id):
    updated_data = request.get_json()
    new_username = updated_data.get("username")
    new_password = updated_data.get("password")
    new_email = updated_data.get("email")
    updated_fields = dict()

    if new_username:
        updated_fields["username"] = new_username
    if new_password:
        updated_fields["password"] = new_password
    if new_email:
        updated_fields["email"] = new_email

    update_result = sql_db.update_user(user_id, **updated_fields)
    if update_result:
        return jsonify({"message": f"User{user_id} updated"}), 201
    else:
        return jsonify({"error": f"Can not update User{user_id}"}), 400


# delete
# delete user
@users_bp.route("/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    success = sql_db.delete_user(user_id)
    if success:
        return jsonify({"message": f"User{user_id} deleted"}), 204
    else:
        return jsonify({"error": f"Can not delete User{user_id}"}), 400


# def delete_custom_bot_from_user(engine, user_id, bot_id)
@users_bp.route("/<int:user_id>/<int:bot_id>", methods=["DELETE"])
def delete_custom_bot_from_user(user_id, bot_id):
    success = sql_db.delete_custom_bot_from_user(user_id, bot_id)
    if success:
        return jsonify({"message": f"Custom Bot{bot_id} deleted from user {user_id}"}), 204
    else:
        return jsonify({"error": f"Can not delete Custom Bot{bot_id} from user {user_id}"}), 400
