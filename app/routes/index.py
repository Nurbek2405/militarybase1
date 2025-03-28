from flask import render_template, request
from app.models import calculate_expiry
from datetime import datetime

def index():
    from main import db, Employee, PREFLIGHT_CONDITIONS  # Импорт внутри функции

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
        db.session.refresh(emp)  # Синхронизируем объект с базой
        expiry_data = calculate_expiry(emp)  # Пересчитываем для каждого сотрудника
        employees_with_expiry.append(expiry_data)

    # Сохраняем изменения в базе (например, preflight_condition)
    for emp in employees_with_expiry:
        db.session.add(emp['employee'])
    db.session.commit()

    if sort == 'deadline_asc':
        employees_with_expiry.sort(
            key=lambda x: x['min_days_left'] if x['min_days_left'] is not None else float('inf'),
            reverse=False)  # Сортировка по возрастанию, без reverse=True

    return render_template(
        'index.html',
        employees_with_expiry=employees_with_expiry,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        datetime=datetime,
        preflight_conditions=PREFLIGHT_CONDITIONS
    )