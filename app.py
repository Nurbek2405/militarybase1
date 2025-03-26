from flask import Flask
from pyngrok import ngrok
import os
from flask_sqlalchemy import SQLAlchemy
from routes import register_routes
from datetime import datetime, timedelta

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6')
base_dir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(base_dir, 'instance')
os.makedirs(instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_path, 'medical_db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Определяем модели прямо здесь, чтобы избежать циклического импорта
PREFLIGHT_CONDITIONS = ['Допущен', 'Отстранен']
EXAM_TYPES = ['ВЛК', 'КМО', 'УМО', 'КМО2']

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fio = db.Column(db.String(100), nullable=False, unique=True)
    birth_date = db.Column(db.Date, nullable=False)
    position = db.Column(db.String(100), nullable=False)
    order_no = db.Column(db.String(50), nullable=False)
    preflight_condition = db.Column(db.String(100), default='Допущен')
    note = db.Column(db.String(200))
    examinations = db.relationship('Examination', backref='employee', lazy=True, cascade='all, delete')

class Examination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)
    exam_date = db.Column(db.Date, nullable=False)
    diagnosis = db.Column(db.String(200))

register_routes(app)  # Регистрация маршрутов после определения моделей

with app.app_context():
    db.create_all()

if os.getenv('FLASK_RUN_PORT') == '5000':
    port = 5000
    public_url = ngrok.connect(port).public_url
    print(f"Ngrok tunnel: {public_url}")
else:
    port = int(os.getenv('FLASK_RUN_PORT', 5000))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=port)