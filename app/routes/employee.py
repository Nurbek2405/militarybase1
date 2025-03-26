from flask import render_template, request, redirect, url_for, flash
from app.models import process_employee_form, calculate_expiry, recalculate_all_employees

def add():
    from app.main import db, Employee, Examination, PREFLIGHT_CONDITIONS

    if request.method == 'POST':
        try:
            employee_data, examinations = process_employee_form(request.form)
            if not all([employee_data['fio'], employee_data['birth_date'], employee_data['position'],
                        employee_data['order_no']]):
                flash('Поля ФИО, дата рождения, должность и "По приказу № 721" обязательны!', 'danger')
                return redirect(url_for('add'))

            existing_employee = Employee.query.filter_by(fio=employee_data['fio']).first()
            if existing_employee:
                flash(f'Сотрудник с ФИО "{employee_data["fio"]}" уже существует!', 'danger')
                return redirect(url_for('add'))

            employee = Employee(**employee_data)
            db.session.add(employee)
            db.session.flush()

            for exam in examinations:
                db.session.add(Examination(employee_id=employee.id, **exam))

            recalculate_all_employees(db.session)  # Пересчитываем всех сотрудников
            flash('Сотрудник успешно добавлен!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Ошибка добавления сотрудника: {str(e)}", 'danger')
            return redirect(url_for('add'))

    return render_template('add.html', preflight_conditions=PREFLIGHT_CONDITIONS)

def edit(id):
    from app.main import db, Employee, Examination, PREFLIGHT_CONDITIONS

    employee = Employee.query.get_or_404(id)
    if request.method == 'POST':
        try:
            employee_data, examinations = process_employee_form(request.form)
            if not all([employee_data['fio'], employee_data['birth_date'], employee_data['position'],
                        employee_data['order_no']]):
                flash('Поля ФИО, дата рождения, должность и "По приказу № 721" обязательны!', 'danger')
                return redirect(url_for('edit', id=id))

            existing_employee = Employee.query.filter(Employee.fio == employee_data['fio'],
                                                      Employee.id != id).first()
            if existing_employee:
                flash(f'Сотрудник с ФИО "{employee_data["fio"]}" уже существует!', 'danger')
                return redirect(url_for('edit', id=id))

            for key, value in employee_data.items():
                setattr(employee, key, value)
            Examination.query.filter_by(employee_id=id).delete()
            for exam in examinations:
                db.session.add(Examination(employee_id=id, **exam))

            recalculate_all_employees(db.session)  # Пересчитываем всех сотрудников
            flash('Данные сотрудника успешно обновлены!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Ошибка обновления данных: {str(e)}", 'danger')
            return redirect(url_for('edit', id=id))

    examinations = Examination.query.filter_by(employee_id=id).all()
    return render_template('edit.html', employee=employee, examinations=examinations,
                           preflight_conditions=PREFLIGHT_CONDITIONS)

def history(id):
    from app.main import db, Employee, Examination

    employee = Employee.query.get_or_404(id)
    examinations = Examination.query.filter_by(employee_id=id).order_by(Examination.exam_date.asc()).all()
    return render_template('history.html', employee=employee, examinations=examinations)

def delete(id):
    from app.main import db, Employee

    employee = Employee.query.get_or_404(id)
    try:
        db.session.delete(employee)
        recalculate_all_employees(db.session)  # Пересчитываем всех сотрудников
        flash('Сотрудник успешно удален!', 'success')
    except Exception as e:
        flash(f"Ошибка удаления сотрудника: {str(e)}", 'danger')
    return redirect(url_for('index'))