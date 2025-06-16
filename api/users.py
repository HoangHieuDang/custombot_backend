from database import database_handling as db
from flask import Blueprint, request, jsonify, session
from api.extensions import bcrypt

users_bp = Blueprint("users", __name__)
sql_db = db.SQLiteDataManager("./database/custom_bot_db")


# create
# USER_REGISTRATION
@users_bp.route("/register", methods=["POST"])
def create_user():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not all([username, email, password]):
        return jsonify({"error": "Missing required fields."}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    new_user = [{
        "username": username,
        "email": email.strip().lower(),
        "password": hashed_password
    }]

    success = sql_db.add_user(new_user)
    if success:
        return jsonify({"message": "User created successfully."}), 201
    else:
        return jsonify({"error": "User creation failed. Username or email may already exist."}), 400


# USER_LOGIN
@users_bp.route("/login", methods=["POST"])
def login_user():
    email = request.json.get("email")
    password = request.json.get("password")
    logined_user = sql_db.get_login_user(email, password)
    if not logined_user:
        print("Unauthorized branch hit")
        return jsonify({"error": "Unauthorized"}), 401
    session["user_id"] = int(logined_user)
    return jsonify({"id": logined_user, "email": email})


# USER_LOGOUT
@users_bp.route("/logout", methods=["POST"])
def logout_user():
    session.pop("user_id", None)
    return jsonify({"message": "Logged out"}), 200


# read
# Get current loging in user
@users_bp.route("/@me", methods=["GET"])
def get_current_login_user():
    print("we get into the current login user route here")
    user_id = session.get("user_id")
    print("user_id given by @me route: ", user_id)
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    current_user = sql_db.get_current_login_user_info(user_id)
    if not current_user:
        return jsonify({"error": "User not found"}), 404

    print("Session at login:", dict(session))
    return jsonify({"id": current_user["user_id"], "email": current_user["email"]})


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
