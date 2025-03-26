from flask import Flask
from app.routes.index import index
from app.routes.employee import add, edit, history, delete
from app.routes.excel import export_excel_xlsx, export_excel_xls, import_excel

def register_routes(app: Flask):
    app.route('/')(index)
    app.route('/add', methods=['GET', 'POST'])(add)
    app.route('/edit/<int:id>', methods=['GET', 'POST'])(edit)
    app.route('/history/<int:id>')(history)
    app.route('/delete/<int:id>')(delete)
    app.route('/export_excel_xlsx')(export_excel_xlsx)
    app.route('/export_excel_xls')(export_excel_xls)
    app.route('/import_excel', methods=['GET', 'POST'])(import_excel)