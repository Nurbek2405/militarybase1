from flask import render_template, request
from flask_login import login_required
from app.models import calculate_expiry
from datetime import datetime
from models import db, Employee, AuditLog, PREFLIGHT_CONDITIONS

@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    sort = request.args.get('sort', 'deadline_asc')
    search = request.args.get('search', '')

    query = Employee.query
    if search:
        query = query.filter(Employee.fio.ilike(f'%{search}%'))

    if sort == 'fio_asc':
        query = query.order_by(Employee.fio.asc())
    elif sort == 'fio_desc':
        query = query.order_by(Employee.fio.desc())
    elif sort == 'suspended':
        query = query.filter(Employee.preflight_condition == 'Отстранен')
    elif sort == 'deadline_asc':
        pass

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    employees = pagination.items
    total_pages = pagination.pages

    employees_with_expiry = []
    for emp in employees:
        db.session.refresh(emp)
        expiry_data = calculate_expiry(emp)
        employees_with_expiry.append(expiry_data)

    for emp in employees_with_expiry:
        db.session.add(emp['employee'])
    db.session.commit()

    if sort == 'deadline_asc':
        employees_with_expiry.sort(
            key=lambda x: x['min_days_left'] if x['min_days_left'] is not None else float('inf'),
            reverse=False)

    return render_template(
        'index.html',
        employees_with_expiry=employees_with_expiry,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        datetime=datetime,
        preflight_conditions=PREFLIGHT_CONDITIONS
    )

@login_required
def logs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('logs.html', logs=logs)