from flask import Flask
from api.users import users_bp
from api.bots import bots_bp
from api.parts import parts_bp
from api.orders import orders_bp
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.register_blueprint(users_bp, url_prefix="/users")
app.register_blueprint(bots_bp, url_prefix="/custom_bots")
app.register_blueprint(parts_bp, url_prefix="/parts")
app.register_blueprint(orders_bp, url_prefix="/orders")

if __name__ == "__main__":
    app.run(debug=True)
