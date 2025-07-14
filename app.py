from flask import Flask
from api.users import users_bp
from api.bots import bots_bp
from api.parts import parts_bp
from api.orders import orders_bp
from flask_session import Session
from api.extensions import bcrypt
from flask_cors import CORS
from api.config import ApplicationConfig

# Create app
app = Flask(__name__)
app.config.from_object(ApplicationConfig)
# Apply CORS before registering blueprints
CORS(
    app,
    origins=["http://127.0.0.1:5173"],
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

if __name__ == "__main__":
    #app.run(debug=True, host="127.0.0.1")
    app.run()
