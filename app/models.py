from datetime import datetime, timedelta

def process_employee_form(form):
    from main import PREFLIGHT_CONDITIONS, EXAM_TYPES
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
                    'diagnosis': form.get(diag_key),
                    'note': None  # Примечание для осмотров не используется
                })
            except ValueError:
                print(f"Ошибка формата даты для {exam_type}: {form[date_key]}")
    return employee_data, examinations

def calculate_expiry(employee):
    from main import EXAM_TYPES
    latest_exam_dates = {exam_type: None for exam_type in EXAM_TYPES}
    expiry_dates = {exam_type: None for exam_type in EXAM_TYPES}
    days_left = {exam_type: float('inf') for exam_type in EXAM_TYPES}
    forecast_dates = {exam_type: None for exam_type in EXAM_TYPES}  # Прогнозные даты
    nearest_exam = None
    min_days_left = float('inf')

    # Находим последнюю дату для каждого типа осмотра
    for exam in employee.examinations:
        if exam.exam_type in EXAM_TYPES:
            if not latest_exam_dates[exam.exam_type] or exam.exam_date > latest_exam_dates[exam.exam_type]:
                latest_exam_dates[exam.exam_type] = exam.exam_date

    current_date = datetime.now().date()
    vlk_date = latest_exam_dates['ВЛК']

    # Базовые сроки от ВЛК, если ВЛК есть
    if vlk_date:
        expiry_dates['ВЛК'] = vlk_date + timedelta(days=365)  # 365 дней от ВЛК
        expiry_dates['КМО'] = vlk_date + timedelta(days=90)   # 90 дней от ВЛК
        expiry_dates['УМО'] = vlk_date + timedelta(days=180)  # 180 дней от ВЛК
        expiry_dates['КМО2'] = vlk_date + timedelta(days=270) # 270 дней от ВЛК

    # Переопределяем сроки, если есть более поздние даты осмотров
    for exam_type in EXAM_TYPES:
        if latest_exam_dates[exam_type] and (not vlk_date or latest_exam_dates[exam_type] > vlk_date):
            expiry_dates[exam_type] = latest_exam_dates[exam_type] + timedelta(days=365)  # 365 дней от последнего осмотра

    # Рассчитываем дни до окончания для каждого типа осмотра
    for exam_type in EXAM_TYPES:
        if expiry_dates[exam_type]:
            days_left[exam_type] = (expiry_dates[exam_type] - current_date).days
            if days_left[exam_type] < min_days_left:
                min_days_left = days_left[exam_type]
                nearest_exam = exam_type

    # Рассчитываем прогнозные даты для осмотров
    # Если есть фактическая дата ВЛК, используем её как базовую
    if vlk_date:
        forecast_dates['ВЛК'] = vlk_date + timedelta(days=365)  # Следующий ВЛК через год
        forecast_dates['КМО'] = vlk_date + timedelta(days=90)   # КМО через 3 месяца
        forecast_dates['УМО'] = vlk_date + timedelta(days=180)  # УМО через 6 месяцев
        forecast_dates['КМО2'] = vlk_date + timedelta(days=270) # КМО2 через 9 месяцев

    # Если есть более поздние фактические осмотры, корректируем прогнозы
    for exam_type in EXAM_TYPES:
        if latest_exam_dates[exam_type] and (not vlk_date or latest_exam_dates[exam_type] > vlk_date):
            if exam_type == 'ВЛК':
                forecast_dates['ВЛК'] = latest_exam_dates['ВЛК'] + timedelta(days=365)
                forecast_dates['КМО'] = latest_exam_dates['ВЛК'] + timedelta(days=90)
                forecast_dates['УМО'] = latest_exam_dates['ВЛК'] + timedelta(days=180)
                forecast_dates['КМО2'] = latest_exam_dates['ВЛК'] + timedelta(days=270)
            elif exam_type == 'КМО':
                forecast_dates['КМО'] = latest_exam_dates['КМО'] + timedelta(days=365)
            elif exam_type == 'УМО':
                forecast_dates['УМО'] = latest_exam_dates['УМО'] + timedelta(days=365)
            elif exam_type == 'КМО2':
                forecast_dates['КМО2'] = latest_exam_dates['КМО2'] + timedelta(days=365)

    # Если фактическая дата осмотра уже есть, убираем прогноз для этого осмотра
    for exam_type in EXAM_TYPES:
        if latest_exam_dates[exam_type]:
            forecast_dates[exam_type] = None  # Убираем прогноз, если осмотр уже был

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
        'nearest_exam': nearest_exam,
        'vlk_forecast': forecast_dates['ВЛК'],
        'kmo_forecast': forecast_dates['КМО'],
        'umo_forecast': forecast_dates['УМО'],
        'kmo2_forecast': forecast_dates['КМО2']
    }

def recalculate_all_employees(db_session):
    """Пересчитывает сроки для всех сотрудников в базе."""
    from main import Employee
    employees = Employee.query.all()
    for emp in employees:
        db_session.refresh(emp)  # Синхронизируем объект с базой
        expiry_data = calculate_expiry(emp)
        emp.preflight_condition = expiry_data['employee'].preflight_condition
    db_session.commit()