from flask import Flask
from api.users import users_bp
from api.bots import bots_bp
app = Flask(__name__)

app.register_blueprint(users_bp, url_prefix="/users")
app.register_blueprint(bots_bp, url_prefix="/custom_bots")

if __name__ == "__main__":
    app.run(debug=True)
