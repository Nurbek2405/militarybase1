from app import db
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

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

def process_employee_form(form):
    preflight = form['preflight_condition'] if form['preflight_condition'] in PREFLIGHT_CONDITIONS else 'Допущен'
    employee_data = {
        'fio': form['fio'],
        'birth_date': datetime.strptime(form['birth_date'], '%Y-%m-%d') if form['birth_date'] else None,
        'position': form['position'],
        'order_no': form['order_no'],
        'preflight_condition': preflight,
        'note': form['note'] if form['note'] else None
    }
    examinations = []
    for exam_type in EXAM_TYPES:
        date_key = f"{exam_type.lower()}_date"
        diag_key = f"{exam_type.lower()}_diagnosis"
        if form.get(date_key):
            try:
                exam_date = datetime.strptime(form[date_key], '%Y-%m-%d')
                examinations.append({
                    'exam_type': exam_type,
                    'exam_date': exam_date,
                    'diagnosis': form.get(diag_key)
                })
            except ValueError:
                print(f"Ошибка формата даты для {exam_type}: {form[date_key]}")
    return employee_data, examinations

def calculate_expiry(employee):
    latest_exam_dates = {exam_type: None for exam_type in EXAM_TYPES}
    expiry_dates = {exam_type: None for exam_type in EXAM_TYPES}
    days_left = {exam_type: float('inf') for exam_type in EXAM_TYPES}
    nearest_exam = None
    min_days_left = float('inf')

    # Находим последнюю дату для каждого типа осмотра
    for exam in employee.examinations:
        if exam.exam_type in EXAM_TYPES:
            if not latest_exam_dates[exam.exam_type] or exam.exam_date > latest_exam_dates[exam.exam_type]:
                latest_exam_dates[exam.exam_type] = exam.exam_date

    current_date = datetime.now().date()
    vlk_date = latest_exam_dates['ВЛК']

    # Если есть ВЛК, все сроки рассчитываются от него
    if vlk_date:
        expiry_dates['ВЛК'] = vlk_date + relativedelta(months=12)
        expiry_dates['КМО'] = vlk_date + relativedelta(months=3)
        expiry_dates['УМО'] = vlk_date + relativedelta(months=6)
        expiry_dates['КМО2'] = vlk_date + relativedelta(months=9)
    else:
        # Если ВЛК нет, каждый осмотр имеет срок действия 3 месяца до следующего осмотра того же типа
        for exam_type in EXAM_TYPES:
            if latest_exam_dates[exam_type]:
                expiry_dates[exam_type] = latest_exam_dates[exam_type] + relativedelta(months=3)

    # Рассчитываем дни до окончания для каждого типа осмотра
    for exam_type in EXAM_TYPES:
        if expiry_dates[exam_type]:
            days_left[exam_type] = (expiry_dates[exam_type] - current_date).days
            if days_left[exam_type] < min_days_left:
                min_days_left = days_left[exam_type]
                nearest_exam = exam_type

    # Обновляем состояние сотрудника
    if min_days_left < 0 or not employee.examinations:
        employee.preflight_condition = 'Отстранен'
    else:
        employee.preflight_condition = 'Допущен'

    return {
        'employee': employee,
        'vlk_expiry': expiry_dates['ВЛК'],
        'kmo_expiry': expiry_dates['КМО'],
        'umo_expiry': expiry_dates['УМО'],
        'kmo2_expiry': expiry_dates['КМО2'],
        'vlk_days_left': days_left['ВЛК'] if days_left['ВЛК'] != float('inf') else None,
        'kmo_days_left': days_left['КМО'] if days_left['КМО'] != float('inf') else None,
        'umo_days_left': days_left['УМО'] if days_left['УМО'] != float('inf') else None,
        'kmo2_days_left': days_left['КМО2'] if days_left['КМО2'] != float('inf') else None,
        'min_days_left': min_days_left if min_days_left != float('inf') else None,
        'nearest_exam': nearest_exam
    }