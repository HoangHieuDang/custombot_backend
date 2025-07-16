from flask import Flask
from api.users import users_bp
from api.bots import bots_bp
from api.parts import parts_bp
from api.orders import orders_bp
from flask_session import Session
from api.extensions import bcrypt
from flask_cors import CORS
from api.config import ApplicationConfig
from sqlalchemy import inspect
from database.database_handling import data_manager
from database.database_sql_struct import Base
from data.initial_data import bot_parts, parts_metadata

# Create app
app = Flask(__name__)
app.config.from_object(ApplicationConfig)
# Apply CORS before registering blueprints
CORS(
    app,
    origins="*",
    supports_credentials=True,
    expose_headers=["Content-Type", "X-CSRFToken"],
    allow_headers=["Content-Type", "X-CSRFToken"])

Session(app)
bcrypt.init_app(app)


@app.route("/test", methods=["GET"])
def welcome():
    return "Hello, test!"

app.register_blueprint(users_bp, url_prefix="/users")
app.register_blueprint(bots_bp, url_prefix="/custom_bots")
app.register_blueprint(parts_bp, url_prefix="/parts")
app.register_blueprint(orders_bp, url_prefix="/orders")

# add engine to the app config after both app and data_manager are initialized
try:
    app.config['SQLALCHEMY_ENGINE'] = data_manager._engine
except ImportError as err:
    print(f"Could not import data_manager or set engine: {err}")

# Check if the database needs to be initialized
engine = app.config['SQLALCHEMY_ENGINE']
inspector = inspect(engine)

print("Recreating database tables...")
with app.app_context():
    # create the database tables
    Base.metadata.drop_all(engine)  # Drop existing tables if any
    Base.metadata.create_all(engine)
    print(inspector.get_table_names())

    # Add initial data
    data_manager.add_part(bot_parts)
    for part in parts_metadata:
        data_manager.create_part_type_metadata(part['type'], part['is_asymmetrical'])
        print(f"Added part type metadata: {part['type']} (Asymmetrical: {part['is_asymmetrical']})")

    print("Database initialized with body parts.")
print("Database initialized with required tables.")

if __name__ == "__main__":
    # app.run(debug=True, host="127.0.0.1")
    app.run()
