import os
import shutil
import traceback
from flask import Flask
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from pyngrok import ngrok
from models import db, User, PREFLIGHT_CONDITIONS, EXAM_TYPES
from app.routes import register_routes
from datetime import datetime, timedelta
import webbrowser
import sys
from werkzeug.security import generate_password_hash

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6')

    if os.name == 'nt':
        base_dir = os.path.expandvars(r'%APPDATA%\MilitaryBase2')
    else:
        base_dir = os.path.expanduser('~/.militarybase2')
    os.makedirs(base_dir, exist_ok=True)

    db_path = os.path.join(base_dir, 'medical_db.sqlite')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    print("SQLAlchemy initialized with app:", app)

    # Настройка Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    register_routes(app)

    def init_db():
        with app.app_context():
            # Создаем все таблицы, если их нет
            db.create_all()

            # Проверяем и создаем пользователя meduser, если его нет
            if not User.query.filter_by(username='meduser').first():
                user = User(username='meduser')
                user.set_password('akniet1995')
                db.session.add(user)
                db.session.commit()
                print("Создан пользователь meduser")
            else:
                print("Пользователь meduser уже существует")

            print("База данных инициализирована с таблицами:", db_path)

    with app.app_context():
        if not os.path.exists(db_path):
            print("Создана новая база данных:", db_path)
            init_db()
        else:
            print("Используется существующая база данных:", db_path)
            init_db()  # Вызываем init_db() для существующей базы, чтобы добавить новые таблицы

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        from flask import request, render_template, redirect, url_for, flash
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            try:
                user = User.query.filter_by(username=username).first()
                if user and user.check_password(password):
                    login_user(user)
                    next_page = request.args.get('next', url_for('index'))
                    return redirect(next_page)
                else:
                    flash('Неверное имя пользователя или пароль', 'danger')
            except Exception as e:
                flash('Ошибка при входе. Пожалуйста, попробуйте позже.', 'danger')
                print(f"Ошибка в login: {str(e)}")
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    return app

def backup_database(base_dir, db_path):
    if not os.path.exists(db_path):
        print("База данных не найдена, резервная копия не создаётся.")
        return
    backup_dir = os.path.join(base_dir, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'medical_db_backup_{timestamp}.sqlite')
    shutil.copy2(db_path, backup_path)
    print(f"Создана резервная копия: {backup_path}")

    cutoff_date = datetime.now() - timedelta(days=14)
    backups = [f for f in os.listdir(backup_dir) if f.startswith('medical_db_backup_')]
    for backup in backups:
        backup_file = os.path.join(backup_dir, backup)
        file_time_str = backup.split('_')[-2] + '_' + backup.split('_')[-1].replace('.sqlite', '')
        try:
            file_time = datetime.strptime(file_time_str, '%Y%m%d_%H%M%S')
            if file_time < cutoff_date:
                os.remove(backup_file)
                print(f"Удалена старая резервная копия: {backup_file}")
        except ValueError:
            print(f"Не удалось разобрать дату в имени файла: {backup}")

def extract_initial_db(base_dir, db_path):
    if os.path.exists(db_path):
        print("Существующая база данных обнаружена, начальная база не извлекается.")
        return

    if getattr(sys, 'frozen', False):
        bundle_dir = sys._MEIPASS
        initial_db_path = os.path.join(bundle_dir, 'initial_medical_db.sqlite')
        if os.path.exists(initial_db_path):
            shutil.copy2(initial_db_path, db_path)
            print(f"Извлечена начальная база данных в: {db_path}")
        else:
            print("Начальная база данных не найдена в .exe, будет создана пустая база.")

app = create_app()

if __name__ == '__main__':
    try:
        base_dir = os.path.expandvars(r'%APPDATA%\MilitaryBase2') if os.name == 'nt' else os.path.expanduser('~/.militarybase2')
        db_path = os.path.join(base_dir, 'medical_db.sqlite')
        extract_initial_db(base_dir, db_path)
        backup_database(base_dir, db_path)
        port = int(os.getenv('FLASK_RUN_PORT', 5000))
        if port == 5000 and os.getenv('USE_NGROK', '0') == '1':
            public_url = ngrok.connect(port).public_url
            print(f"Ngrok tunnel: {public_url}")
            webbrowser.open(public_url)
        else:
            local_url = f"http://127.0.0.1:{port}"
            print(f"Running locally at: {local_url}")
            webbrowser.open(local_url)
        app.run(debug=False, host='0.0.0.0', port=port)
    except Exception as e:
        print("Произошла ошибка:")
        traceback.print_exc()
        input("Нажмите Enter для завершения...")