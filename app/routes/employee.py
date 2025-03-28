from flask import render_template, request, redirect, url_for, flash
from app.models import process_employee_form, recalculate_all_employees
from datetime import timedelta  # Добавляем импорт timedelta

def add():
    from main import db, Employee, Examination, PREFLIGHT_CONDITIONS

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
            db.session.commit()  # Явно фиксируем изменения
            flash('Сотрудник успешно добавлен!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Ошибка добавления сотрудника: {str(e)}", 'danger')
            print(f"Ошибка в add(): {str(e)}")  # Добавляем отладочный вывод
            return redirect(url_for('add'))

    return render_template('add.html', preflight_conditions=PREFLIGHT_CONDITIONS)

def edit(id):
    from main import db, Employee, Examination, PREFLIGHT_CONDITIONS

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
            db.session.commit()  # Явно фиксируем изменения
            flash('Данные сотрудника успешно обновлены!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Ошибка обновления данных: {str(e)}", 'danger')
            print(f"Ошибка в edit(): {str(e)}")  # Добавляем отладочный вывод
            return redirect(url_for('edit', id=id))

    examinations = Examination.query.filter_by(employee_id=id).all()
    return render_template('edit.html', employee=employee, examinations=examinations,
                           preflight_conditions=PREFLIGHT_CONDITIONS)

def history(id):
    from main import Employee, Examination

    employee = Employee.query.get_or_404(id)
    examinations = Examination.query.filter_by(employee_id=id).order_by(Examination.exam_date.asc()).all()

    # Создаём список осмотров с рассчитанным сроком действия
    examinations_with_expiry = []
    for exam in examinations:
        # Рассчитываем срок действия в зависимости от типа осмотра
        days_to_add = 365 if exam.exam_type == 'ВЛК' else 90 if exam.exam_type == 'КМО' else 180 if exam.exam_type == 'УМО' else 270 if exam.exam_type == 'КМО2' else 0
        expiry_date = exam.exam_date + timedelta(days=days_to_add) if exam.exam_date else None
        examinations_with_expiry.append({
            'exam': exam,
            'expiry_date': expiry_date
        })

    return render_template('history.html', employee=employee, examinations_with_expiry=examinations_with_expiry)

def delete(id):
    from main import db, Employee

    employee = Employee.query.get_or_404(id)
    try:
        db.session.delete(employee)
        recalculate_all_employees(db.session)  # Пересчитываем всех сотрудников
        db.session.commit()  # Явно фиксируем изменения
        flash('Сотрудник успешно удален!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Ошибка удаления сотрудника: {str(e)}", 'danger')
        print(f"Ошибка в delete(): {str(e)}")  # Добавляем отладочный вывод
    return redirect(url_for('index'))