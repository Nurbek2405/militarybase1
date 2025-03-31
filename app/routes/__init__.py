from flask import Flask
from flask_login import login_required
from app.routes.index import index, logs
from app.routes.employee import add, edit, history, delete
from app.routes.excel import export_excel_xlsx, export_excel_xls, import_excel

def register_routes(app: Flask):
    app.route('/')(login_required(index))
    app.route('/add', methods=['GET', 'POST'])(login_required(add))
    app.route('/edit/<int:id>', methods=['GET', 'POST'])(login_required(edit))
    app.route('/history/<int:id>')(login_required(history))
    app.route('/delete/<int:id>')(login_required(delete))
    app.route('/export_excel_xlsx')(login_required(export_excel_xlsx))
    app.route('/export_excel_xls')(login_required(export_excel_xls))
    app.route('/import_excel', methods=['GET', 'POST'])(login_required(import_excel))
    app.route('/logs')(login_required(logs))  # Новый маршрут