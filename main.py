from flask import Flask
from pyngrok import ngrok
import os
from flask_sqlalchemy import SQLAlchemy
from app.routes import register_routes
from datetime import datetime, timedelta

app = Flask(__name__, template_folder='templates') # Явно указываем путь к templates относительно app/

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6')
base_dir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(base_dir, 'instance')
os.makedirs(instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_path, 'medical_db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Определяем модели
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
    note = db.Column(db.String(200))  # Добавляем поле note

register_routes(app)

with app.app_context():
    db.create_all()

port = int(os.getenv('FLASK_RUN_PORT', 5000))  # По умолчанию порт 5000
if port == 5000 and os.getenv('USE_NGROK', '0') == '1':  # Используем ngrok только если явно указано
    public_url = ngrok.connect(port).public_url
    print(f"Ngrok tunnel: {public_url}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=port)