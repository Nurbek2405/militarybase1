from flask import Flask
from pyngrok import ngrok
import os
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6')
base_dir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(base_dir, 'instance')
os.makedirs(instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_path, 'medical_db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

from routes import register_routes
register_routes(app)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port = 9502
    public_url = ngrok.connect(port).public_url  # Открываем туннель ngrok
    print(f"Ngrok tunnel: {public_url}")
    app.run(debug=True, host='0.0.0.0', port=port)