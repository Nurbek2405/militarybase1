from datetime import datetime
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
        note_key = f"{exam_type.lower()}_note"  # Добавляем ключ для примечания
        if form.get(date_key):
            try:
                exam_date = datetime.strptime(form[date_key], '%Y-%m-%d')
                examinations.append({
                    'exam_type': exam_type,
                    'exam_date': exam_date,
                    'diagnosis': form.get(diag_key),
                    'note': form.get(note_key) if form.get(note_key) else None  # Добавляем примечание
                })
            except ValueError:
                print(f"Ошибка формата даты для {exam_type}: {form[date_key]}")
    return employee_data, examinations