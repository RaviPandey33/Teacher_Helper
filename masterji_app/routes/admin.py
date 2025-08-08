from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
import logging
logging.basicConfig(level=logging.DEBUG)

import json
from extensions import db
from models.student import Student

from models.attendance import Attendance
from models.payment import Payment
from forms.student_form import AddStudentForm
from forms.attendance_form import AttendanceForm
from forms.payment_form import MonthlyPaymentForm
from datetime import date, datetime, timedelta
from forms.attendance_by_name_form import AttendanceByNameForm
from flask import jsonify
from models.reschedule import TemporaryClass, SkippedClass
from datetime import datetime, timedelta

def convert_pst_to_ist_time_and_day(hour, minute, am_pm, current_day):
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_index = day_order.index(current_day)

    # Convert to 24hr
    hour = int(hour)
    minute = int(minute)
    if am_pm.upper() == 'PM' and hour != 12:
        hour += 12
    if am_pm.upper() == 'AM' and hour == 12:
        hour = 0

    pst_time = datetime(2000, 1, 1, hour, minute)
    ist_time = pst_time + timedelta(hours=12, minutes=30)

    # Day rollover check
    new_day_index = (day_index + 1) % 7 if ist_time.day != pst_time.day else day_index
    new_day = day_order[new_day_index]
    ist_time_str = ist_time.strftime('%I:%M %p')

    return new_day, ist_time_str


import json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route("/admin/debug_class_times")
def debug_class_times():
    students = Student.query.all()
    result = []

    for s in students:
        try:
            class_times = json.loads(s.class_time_raw) if s.class_time_raw else {}
        except Exception as e:
            class_times = f"Error parsing: {e}"

        result.append(f"<strong>{s.name}</strong>: {class_times}<br>")

    return "<br>".join(result)


@admin_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('admin_dashboard.html', user=current_user)

@admin_bp.route('/admin/credits', methods=['GET', 'POST'])
@login_required
def credits_dashboard():
    students = Student.query.all()
    return render_template('credits_dashboard.html', students=students)


@admin_bp.route('/update_credit/<int:student_id>', methods=['POST'])
@login_required
def update_credit(student_id):
    from models import Student  # just in case
    data = request.get_json()
    delta = data.get("delta")

    student = Student.query.get_or_404(student_id)

    if delta == "reset":
        student.reschedule_credits = 0
    else:
        delta = int(delta)
        student.reschedule_credits = max(0, student.reschedule_credits + delta)

    db.session.commit()
    return jsonify(success=True, credits=student.reschedule_credits)



@admin_bp.route('/add-student', methods=['GET', 'POST'])
@login_required
def add_student():
    form = AddStudentForm()

    if form.validate_on_submit():
        # Handle "Not Fix" case by storing as 0
        raw_value = form.classes_per_week.data
        selected_count = 0 if raw_value == "Not Fix" else int(raw_value)

        class_times = []
        if selected_count > 0:
            for i in range(selected_count):
                time = form.class_times.entries[i]
                class_times.append({
                    "days": [time.form.day.data],
                    "hour": time.form.hour.data,
                    "minute": time.form.minute.data,
                    "am_pm": time.form.am_pm.data.upper()
                })

        class_time_json = json.dumps(class_times)

        new_student = Student(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            student_country_code=form.student_country_code.data,
            parent_name=form.parent_name.data,
            parent_email=form.parent_email.data,
            parent_phone=form.parent_phone.data,
            parent_country_code=form.parent_country_code.data,
            discord_id=form.discord_id.data,
            sibling_reference=form.sibling_reference.data,
            learning_subject=form.learning_subject.data,
            fee_per_month=form.fee_per_month.data,
            notes=form.notes.data,
            gender=form.gender.data,
            residing_country=form.residing_country.data,
            zoom_link=form.zoom_link.data,
            zoom_password=form.zoom_password.data,

            # Class details
            classes_per_week=selected_count,
            timezone=form.timezone.data,
            class_time_raw=class_time_json,

            # Profile
            date_of_birth=form.date_of_birth.data,
            grade=form.grade.data,
            school_name=form.school_name.data,
            hobbies=form.hobbies.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,

            # Future goals
            future_college=form.future_college.data,
            future_stream=form.future_stream.data,
            career_interest=form.career_interest.data
        )

        db.session.add(new_student)
        db.session.commit()
        flash('✅ Student added successfully!', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('add_student.html', form=form)



def parse_class_times(raw):
    class_times = []
    if raw:
        entries = [e.strip() for e in raw.split(',') if e.strip()]
        for entry in entries:
            parts = entry.split(' ', 1)
            if len(parts) == 2 and parts[0] in ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']:
                class_times.append(entry)
            else:
                class_times.append("⚠️ Invalid class time entry")
    else:
        class_times = ["⚠️ Invalid class time entry"]
    return class_times

from flask import jsonify
@admin_bp.route('/cancel_temp_class', methods=['POST'])
@login_required
def cancel_temp_class():
    

    data = request.get_json()
    class_id = data.get('class_id')

    if not class_id:
        return jsonify({'success': False, 'message': 'Missing class ID'}), 400

    temp_class = TemporaryClass.query.get(class_id)
    if not temp_class:
        return jsonify({'success': False, 'message': 'Class not found'}), 404

    # ✅ Mark it as cancelled
    temp_class.is_cancelled = True
    db.session.commit()

    return jsonify({'success': True, 'message': 'Temporary class cancelled'})




@admin_bp.route('/skip_regular_class', methods=['POST'])
@login_required
def skip_regular_class():
    print("****************************We are skip****************************")
    try:
        student_id = request.form.get('student_id')
        class_date = request.form.get('class_date')
        class_time = request.form.get('class_time')

        # 🔥 validate format
        class_date_obj = datetime.strptime(class_date, "%Y-%m-%d")
        new_skip = SkippedClass(student_id=student_id, class_date=class_date_obj, class_time=class_time)
        db.session.add(new_skip)
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        print("Error skipping class:", e)
        return jsonify({'status': 'error'}), 500



@admin_bp.route('/students', methods=['GET', 'POST'])
@login_required
def student_list():
    query = request.args.get('q', '').strip()
    if query:
        students = Student.query.filter(
            (Student.parent_email.ilike(f"%{query}%")) |
            (Student.parent_phone.ilike(f"%{query}%"))
        ).order_by(Student.name.asc()).all()
        flash(f"Showing results for: {query}", "info")
    else:
        students = Student.query.order_by(Student.name.asc()).all()

    # ✅ Add this loop to attach parsed class times
    for s in students:
        try:
            s.class_times = parse_class_times(s.class_time_raw)
        except Exception as e:
            print(f"[DEBUG] Student: {s.name}, Raw: {s.class_time_raw}, Error: {e}")
            s.class_times = ["⚠️ Invalid class time entry"]


    return render_template('student_list.html', students=students, search_query=query)

@admin_bp.route('/student/<int:student_id>/deactivate', methods=['POST'])
@login_required
def deactivate_student(student_id):
    student = Student.query.get_or_404(student_id)
    student.status = 'inactive'
    db.session.commit()
    flash(f'{student.name} marked as inactive.', 'info')
    return redirect(url_for('admin.student_list'))

@admin_bp.route('/student/<int:student_id>/activate', methods=['POST'])
@login_required
def activate_student(student_id):
    student = Student.query.get_or_404(student_id)
    student.status = 'active'
    db.session.commit()
    flash(f'{student.name} is now active again.', 'success')
    return redirect(url_for('admin.student_list'))

@admin_bp.route('/attendance')
@login_required
def attendance_dashboard():
    return render_template('attendance_home.html')

@admin_bp.route('/attendance/mark', methods=['GET', 'POST'])
@login_required
def mark_attendance():
    form = AttendanceForm()
    selected_date = form.date.data
    students = Student.query.filter_by(status='active').order_by(Student.name).all()

    if request.method == 'GET' and not selected_date:
        attendance_data = {}
    else:
        selected_date = selected_date or date.today()
        existing_attendance = Attendance.query.filter_by(date=selected_date).all()
        attendance_data = {record.student_id: record.status for record in existing_attendance}

    if request.method == 'POST' and form.validate_on_submit():
        for student in students:
            status_key = f'status_{student.id}'
            status = request.form.get(status_key)
            if status in ['Present', 'Absent']:
                record = Attendance.query.filter_by(student_id=student.id, date=selected_date).first()

                if not record:
                    # New attendance entry
                    record = Attendance(student_id=student.id, date=selected_date, status=status)
                    db.session.add(record)
                    if status == 'Absent':
                        student.reschedule_credits += 1  # First-time absence
                else:
                    # Existing record — check if it changed from Present to Absent
                    if record.status != status:
                        if record.status == 'Present' and status == 'Absent':
                            student.reschedule_credits += 1
                        elif record.status == 'Absent' and status == 'Present':
                            student.reschedule_credits = max(0, student.reschedule_credits - 1)
                    record.status = status  # Update the record either way

        db.session.commit()
        flash('Attendance saved.', 'success')
        return redirect(url_for('admin.mark_attendance'))

    return render_template(
        'attendance.html',
        form=form,
        students=students,
        selected_date=selected_date,
        attendance_data=attendance_data
    )


@admin_bp.route('/attendance/view', methods=['GET', 'POST'])
@login_required
def view_attendance():
    form = AttendanceForm()
    selected_date = form.date.data or date.today()
    students = Student.query.order_by(Student.name.asc()).all()

    attendance_data = {record.student_id: record.status
                       for record in Attendance.query.filter_by(date=selected_date).all()}

    return render_template('attendance_view.html', form=form,
                           students=students, attendance_data=attendance_data,
                           selected_date=selected_date)

@admin_bp.route('/attendance/by-name', methods=['GET', 'POST'])
@login_required
def attendance_by_name():
    form = AttendanceByNameForm()
    all_students = Student.query.order_by(Student.name).all()
    
    selected_student = None
    attendance_data = []
    selected_month = None

    if request.method == 'POST':
        query = request.form.get('student_query', '').split('(')[0].strip()
        selected_month = request.form.get('month')

        if query and selected_month:
            selected_student = Student.query.filter(Student.name.ilike(f"%{query}%")).first()
            if selected_student:
                month_start = datetime.strptime(selected_month + "-01", "%Y-%m-%d").date()
                month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
                attendance_data = Attendance.query.filter(
                    Attendance.student_id == selected_student.id,
                    Attendance.date >= month_start,
                    Attendance.date < month_end
                ).order_by(Attendance.date).all()

    return render_template('attendance_by_name.html',
                           form=form,
                           all_students=all_students,
                           student=selected_student,
                           attendance_data=attendance_data,
                           selected_month=selected_month)




@admin_bp.route('/payments')
@login_required
def payment_dashboard():
    return render_template('payments_home.html')

@admin_bp.route('/payments/update', methods=['GET', 'POST'])
@login_required
def update_current_payments():
    form = MonthlyPaymentForm()
    current_month = date.today().strftime('%Y-%m')
    form.month.data = date.today()
    students = Student.query.order_by(Student.name).all()

    if request.method == 'POST':
        selected_month = request.form.get('month')
        if selected_month:
            for student in students:
                status_key = f'status_{student.id}'
                status = request.form.get(status_key)
                if status:
                    record = Payment.query.filter_by(student_id=student.id, month=selected_month).first()
                    if not record:
                        record = Payment(student_id=student.id, month=selected_month)
                        db.session.add(record)
                    record.status = status
            db.session.commit()
            flash(f'Payments updated for {selected_month}.', 'success')
            return redirect(url_for('admin.payment_dashboard'))

    payment_data = {
        p.student_id: p.status
        for p in Payment.query.filter_by(month=current_month).all()
    }

    return render_template('payments_update.html', form=form, students=students,
                           payment_data=payment_data, selected_month=current_month)

@admin_bp.route('/payments/view', methods=['GET', 'POST'])
@login_required
def view_past_payments():
    form = MonthlyPaymentForm()
    selected_month = None
    payment_data = {}
    students = Student.query.order_by(Student.name).all()

    if request.method == 'POST':
        selected_month = request.form.get('month')
        if selected_month:
            payment_data = {
                p.student_id: p.status
                for p in Payment.query.filter_by(month=selected_month).all()
            }

    return render_template('payments_view.html', form=form,
                           students=students,
                           payment_data=payment_data,
                           selected_month=selected_month)


@admin_bp.route('/payments/summary')
@login_required
def view_payment_summary():
    students = Student.query.order_by(Student.name).all()

    # Get last 5 months from today
    today = date.today()
    month_keys = [(today.replace(day=1) - timedelta(days=30 * i)).strftime('%Y-%m') for i in range(5)][::-1]
    month_labels = [(today.replace(day=1) - timedelta(days=30 * i)).strftime('%b %Y') for i in range(5)][::-1]

    payments_by_student = {}
    for student in students:
        records = Payment.query.filter(
            Payment.student_id == student.id,
            Payment.month.in_(month_keys)
        ).all()
        status_map = {r.month: r.status for r in records}
        row = {m: status_map.get(m, 'NA') for m in month_keys}
        payments_by_student[student.id] = row

    return render_template('payments_summary.html',
                           students=students,
                           month_keys=month_keys,
                           month_labels=month_labels,
                           payments_by_student=payments_by_student)



@admin_bp.route('/student/<int:student_id>/delete', methods=['POST'])
@login_required
def delete_student(student_id):
    from models import Student, TemporaryClass, SkippedClass, Attendance
    from extensions import db

    student = Student.query.get_or_404(student_id)

    # Clean up all dependent data
    TemporaryClass.query.filter_by(student_id=student.id).delete()
    SkippedClass.query.filter_by(student_id=student.id).delete()
    Attendance.query.filter_by(student_id=student.id).delete()

    # Delete student
    db.session.delete(student)
    db.session.commit()

    flash(f"✅ Deleted student '{student.name}' and all related data.", "success")
    return redirect(url_for('admin.view_students'))  # or wherever you want to go

from flask import request
# from pytz import timezone as pytz_timezone
from datetime import timedelta
from datetime import datetime, timedelta
from collections import defaultdict


@admin_bp.route('/schedule')
@login_required
def class_schedule():
    from collections import defaultdict
    from datetime import datetime, timedelta, date
    import json
    from models.reschedule import TemporaryClass
    from models.attendance import Attendance

    tz_choice = request.args.get('tz', 'PST')
    is_ist = tz_choice == 'IST'
    week_offset = int(request.args.get('week', 0))

    all_students = Student.query.filter_by(status='active').all()
    weekly_schedule = defaultdict(list)
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    base_date = date.today() + timedelta(weeks=week_offset)
    monday = base_date - timedelta(days=base_date.weekday())
    sunday = monday + timedelta(days=6)

    # ✅ Day label map
    day_dates = {
        day: (monday + timedelta(days=i)).strftime('%Y-%m-%d')
        for i, day in enumerate(days_order)
    }

    # ✅ Fetch attendance for the week
    attendance_records = Attendance.query.filter(
        Attendance.date >= monday,
        Attendance.date <= sunday
    ).all()
    attendance_map = {(a.student_id, a.date): a.status for a in attendance_records}

    # ✅ Fetch temp classes
    active_ids = [s.id for s in all_students]
    temp_classes = TemporaryClass.query.filter(
        TemporaryClass.date >= monday,
        TemporaryClass.date <= sunday,
        TemporaryClass.student_id.in_(active_ids),
        TemporaryClass.is_cancelled == False
    ).all()

    # ✅ Fetch skipped regulars
    skipped_entries = SkippedClass.query.filter(
        SkippedClass.date >= monday,
        SkippedClass.date <= sunday
    ).all()
    skipped_map = {(s.student_id, s.date): True for s in skipped_entries}

    # ✅ Process regular classes
    for student in all_students:
        if not student.class_time_raw:
            continue

        try:
            class_times = json.loads(student.class_time_raw)
        except Exception:
            class_times = []

        for ct in class_times:
            if not isinstance(ct, dict) or not ct.get('days') or not ct.get('hour') or not ct.get('minute') or not ct.get('am_pm'):
                continue

            day = ct['days'][0] if isinstance(ct['days'], list) else ct['days']
            try:
                hour = int(ct['hour'])
                minute = int(ct['minute'])
                am_pm = ct['am_pm'].upper()
            except (KeyError, ValueError):
                continue

            if am_pm == 'PM' and hour != 12:
                hour += 12
            if am_pm == 'AM' and hour == 12:
                hour = 0

            pst_time = datetime(2000, 1, 1, hour, minute)
            class_date = monday + timedelta(days=days_order.index(day))
            is_skipped = skipped_map.get((student.id, class_date), False)
            status = attendance_map.get((student.id, class_date), None)

            if is_ist:
                ist_time = pst_time + timedelta(hours=12, minutes=30)
                new_day_index = (days_order.index(day) + (1 if ist_time.day != pst_time.day else 0)) % 7
                new_day = days_order[new_day_index]
                display_time = ist_time.strftime('%I:%M %p').lstrip('0')
            else:
                new_day = day
                display_time = pst_time.strftime('%I:%M %p').lstrip('0')

            weekly_schedule[new_day].append({
                'name': student.name,
                'student_id': student.id,
                'time': display_time,
                'zoom_link': student.zoom_link,
                'student': student,
                'is_temp_class': False,
                'is_skipped': is_skipped,
                'status': status
            })

    # ✅ Process temp classes
    for temp in temp_classes:
        student = Student.query.get(temp.student_id)
        if not student:
            continue

        class_day = temp.date.strftime('%A')
        try:
            hour_minute, am_pm = temp.class_time.strip().split(" ")
            hour, minute = map(int, hour_minute.split(":"))
            if am_pm == 'PM' and hour != 12:
                hour += 12
            elif am_pm == 'AM' and hour == 12:
                hour = 0
        except:
            continue

        pst_time = datetime(2000, 1, 1, hour, minute)
        if is_ist:
            ist_time = pst_time + timedelta(hours=12, minutes=30)
            new_day_index = (days_order.index(class_day) + (1 if ist_time.day != pst_time.day else 0)) % 7
            class_day = days_order[new_day_index]
            display_time = ist_time.strftime('%I:%M %p').lstrip('0')
        else:
            display_time = pst_time.strftime('%I:%M %p').lstrip('0')

        temp_status = attendance_map.get((temp.student_id, temp.date), None)

        weekly_schedule[class_day].append({
            'name': f"{student.name} (resched.)",
            'student_id': student.id,
            'time': display_time,
            'zoom_link': temp.zoom_link,
            'student': student,
            'is_temp_class': True,
            'is_skipped': temp.is_cancelled,
            'status': temp_status,
            'id': temp.id
        })

    # Sort entries per day
    for day in weekly_schedule:
        weekly_schedule[day].sort(
            key=lambda entry: datetime.strptime(entry['time'], '%I:%M %p')
        )

    # Current day highlight
    current_day = None
    if week_offset == 0:
        now = datetime.utcnow()
        if is_ist:
            now += timedelta(hours=12, minutes=30)
        current_day = now.strftime('%A')

    return render_template(
        'class_schedule.html',
        schedule=weekly_schedule,
        current_day=current_day,
        tz_choice=tz_choice,
        students=all_students,
        day_dates=day_dates,
        week_offset=week_offset
    )




# @admin_bp.route('/schedule')
# @login_required
# def class_schedule():
#     from collections import defaultdict
#     from datetime import datetime, timedelta, date
#     import json

#     from models.reschedule import TemporaryClass  # ✅ Ensure this import is present

#     tz_choice = request.args.get('tz', 'PST')
#     is_ist = tz_choice == 'IST'

#     all_students = Student.query.filter_by(status='active').all()
#     weekly_schedule = defaultdict(list)
#     days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

#     # # ⏩ Get week offset (e.g., 0 = this week, 1 = next week, -1 = last week)
#     # try:
#     #     week_offset = int(request.args.get('week', 0))
#     # except ValueError:
#     #     week_offset = 0
        
    
    
    
#     # ⏳ Step 1: Add regular weekly classes
#     for student in all_students:
#         if not student.class_time_raw:
#             continue

#         try:
#             class_times = json.loads(student.class_time_raw)
#         except Exception:
#             continue

#         for ct in class_times:
#             day = ct.get('day')
#             if not day:
#                 continue

#             try:
#                 hour = int(ct['hour'])
#                 minute = int(ct['minute'])
#                 am_pm = ct['am_pm'].upper()
#             except (KeyError, ValueError):
#                 continue

#             # Convert to 24-hour format
#             if am_pm == 'PM' and hour != 12:
#                 hour += 12
#             if am_pm == 'AM' and hour == 12:
#                 hour = 0

#             pst_time = datetime(2000, 1, 1, hour, minute)

#             if is_ist:
#                 ist_time = pst_time + timedelta(hours=12, minutes=30)
#                 new_day_index = (days_order.index(day) + (1 if ist_time.day != pst_time.day else 0)) % 7
#                 new_day = days_order[new_day_index]
#                 display_time = ist_time.strftime('%I:%M %p').lstrip('0')
#             else:
#                 new_day = day
#                 display_time = pst_time.strftime('%I:%M %p').lstrip('0')

#             weekly_schedule[new_day].append({
#                 'name': student.name,
#                 'student_id': student.id,
#                 'time': display_time,
#                 'zoom_link': student.zoom_link,
#                 'student': student  # ✅ Required in template
#             })

#     # 📅 Step 2: Add Temporary Rescheduled Classes
#     today = date.today()
#     week_offset = int(request.args.get('week', 0))
#     monday = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
#     sunday = monday + timedelta(days=6)
    
#     week_dates = {}
#     for i, day in enumerate(days_order):
#         current_date = monday + timedelta(days=i)
#         week_dates[day] = current_date.strftime('%-d %B %Y')  # e.g. "7 July 2025"


#     temp_classes = TemporaryClass.query.filter(
#         TemporaryClass.date >= monday,
#         TemporaryClass.date <= sunday
#     ).all()

#     for temp in temp_classes:
#         student = Student.query.get(temp.student_id)
#         if not student:
#             continue

#         class_day = temp.date.strftime('%A')

#         pst_time = datetime(2000, 1, 1, temp.hour, temp.minute)
#         if is_ist:
#             ist_time = pst_time + timedelta(hours=12, minutes=30)
#             new_day_index = (days_order.index(class_day) + (1 if ist_time.day != pst_time.day else 0)) % 7
#             class_day = days_order[new_day_index]
#             display_time = ist_time.strftime('%I:%M %p').lstrip('0')
#         else:
#             display_time = pst_time.strftime('%I:%M %p').lstrip('0')

#         weekly_schedule[class_day].append({
#             'name': f"{student.name} (resched.)",
#             'student_id': student.id,
#             'time': display_time,
#             'zoom_link': temp.zoom_link,
#             'student': student
#         })

#     # ⏰ Sort all entries within each day by time
#     def sort_key(entry):
#         return datetime.strptime(entry['time'], '%I:%M %p')

#     for day in weekly_schedule:
#         weekly_schedule[day].sort(key=sort_key)

    
#     # 📍 Determine current day in selected timezone
#     now = datetime.utcnow() + (timedelta(hours=12, minutes=30) if is_ist else timedelta())
#     current_day = now.strftime('%A')

#     # 📆 Prepare actual dates for each weekday
#     today = date.today()
#     monday = today - timedelta(days=today.weekday())  # Get this week's Monday

#     day_dates = {}
#     for i, weekday in enumerate(days_order):
#         day_date = monday + timedelta(days=i)
#         formatted_date = day_date.strftime('%-d %B %Y')  # e.g., "15 July 2025"
#         day_dates[weekday] = formatted_date

    
#     return render_template('class_schedule.html',
#                        schedule=weekly_schedule,
#                        current_day=current_day,
#                        tz_choice=tz_choice,
#                        students=all_students,
#                        day_dates=day_dates,
#                        week_offset=week_offset)



@admin_bp.route('/add-temp-class', methods=['POST'])
@login_required
def add_temp_class():
    from flask import request, jsonify
    from models.reschedule import TemporaryClass
    from datetime import datetime, timedelta
    from extensions import db
    

    data = request.get_json()
    date_str = data.get('date')  # from frontend

    day = data.get('day')  # 'Monday'
    student_id = data.get('student_id')
    time_str = data.get('time')  # e.g. "14:30"

    if not (day and student_id and time_str):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    try:
        hour, minute = map(int, time_str.split(':'))
        am_pm = 'AM' if hour < 12 else 'PM'
        formatted_hour = hour % 12 or 12  # Convert 0/13–23 to 12-hour format
        class_time_str = f"{formatted_hour:02d}:{minute:02d} {am_pm}"

    except:
        return jsonify({'success': False, 'message': 'Invalid time'}), 400

    # Get date corresponding to the day (for current week)
    today = datetime.utcnow().date()
    monday = today - timedelta(days=today.weekday())
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    try:
        class_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return jsonify({'success': False, 'message': 'Invalid date format'}), 400
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404

    # ✅ Check and deduct credit
    if student.reschedule_credits <= 0:
        return jsonify({'success': False, 'message': 'No reschedule credits available'}), 403

    student.reschedule_credits -= 1

    temp_class = TemporaryClass(
    student_id=student.id,
    class_day=day,  # or class_day=class_day if you're already using that variable
    class_time=class_time_str,  # e.g. "02:00 AM"
    date=class_date,  # datetime.date object
    created_at=datetime.utcnow()
    )

    db.session.add(temp_class)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Class added and credit deducted'})





@admin_bp.route('/attendance/quick-mark', methods=['POST'])
@login_required
def quick_mark_attendance():
    from flask import jsonify

    data = request.json
    student_id = data.get('student_id')
    status = data.get('status')
    date_str = data.get('date')
    is_temp_class = data.get('is_temp_class', False)

    # Validate date
    try:
        attendance_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return jsonify({"success": False, "message": "Invalid date format"}), 400

    student = Student.query.get(student_id)
    if not student:
        return jsonify({"success": False, "message": "Student not found"}), 404

    # 🧹 Clear any existing attendance for that day
    Attendance.query.filter_by(student_id=student.id, date=attendance_date).delete()

    # 🧠 If "Absent" is marked:
    if status == 'Absent':
        # ✅ TEMP CLASS LOGIC
        if is_temp_class:
            temp_class = TemporaryClass.query.filter_by(student_id=student_id, date=attendance_date).first()
            if temp_class:
                temp_class.is_cancelled = True
        else:
            # ✅ REGULAR CLASS LOGIC: Add skip entry
            skip_exists = SkippedClass.query.filter_by(student_id=student_id, date=attendance_date).first()
            if not skip_exists:
                db.session.add(SkippedClass(student_id=student_id, date=attendance_date))

        student.reschedule_credits += 1

    elif status == 'Present':
        # ✅ Optional: Adjust credit if present after previously absent
        existing = Attendance.query.filter_by(student_id=student.id, date=attendance_date, status='Absent').first()
        if existing:
            student.reschedule_credits = max(0, student.reschedule_credits - 1)

    # ✅ Finally, record new attendance
    db.session.add(Attendance(student_id=student.id, date=attendance_date, status=status))
    db.session.commit()

    return jsonify({"success": True, "message": f"Marked {student.name} as {status} on {attendance_date}."})




from datetime import datetime
from models.payment_status import FeeStatus


@admin_bp.route('/payments', methods=['GET', 'POST'])
@login_required
def payments():
    current_month = datetime.now().strftime('%B')
    current_year = datetime.now().year

    students = Student.query.filter_by(status='active').all()
    statuses = {}

    for student in students:
        # Get this month's FeeStatus entry
        status = FeeStatus.query.filter_by(
            student_id=student.id, month=current_month, year=current_year
        ).first()

        # Get unpaid from previous months (not current one)
        unpaid = FeeStatus.query.filter_by(student_id=student.id, payment_done=False).filter(
            (FeeStatus.month != current_month) | (FeeStatus.year != current_year)
        ).all()

        unpaid_months = [f"{s.month} {s.year}" for s in unpaid]
        unpaid_amount = sum(s.amount for s in unpaid)

        # Do not change original student.fee_per_month! Use calculated_fee
        calculated_fee = (student.fee_per_month or 0) + unpaid_amount

        statuses[student.id] = {
            "link_sent": status.link_sent if status else False,
            "payment_done": status.payment_done if status else False,
            "unpaid_months": unpaid_months,
            "unpaid_amount": unpaid_amount,
            "present": status.present if status else 0,
            "absent": status.absent if status else 0,
            "calculated_fee": calculated_fee
        }

    return render_template(
        'payments.html',
        students=students,
        statuses=statuses,
        month=current_month,
        year=current_year
    )



@admin_bp.route('/comments', methods=['GET', 'POST'])
@login_required
def comments():
    students = Student.query.filter_by(status='active').all()
    selected_id = request.form.get("student_id") or request.args.get("student_id")

    new_comment = request.form.get("comment")
    if selected_id and new_comment:
        comment = StudentComment(student_id=int(selected_id), comment=new_comment.strip())
        db.session.add(comment)
        db.session.commit()
        flash("✅ Comment added!", "success")
        return redirect(url_for('admin.comments', student_id=selected_id))

    comments = []
    selected_student = None
    if selected_id:
        selected_student = Student.query.get(int(selected_id))
        comments = StudentComment.query.filter_by(student_id=selected_student.id).order_by(StudentComment.created_at.desc()).all()

    return render_template("student_comments.html", students=students, selected_student=selected_student, comments=comments)



from models.comment import StudentComment
@admin_bp.route('/student-comments/<int:student_id>')
@login_required
def view_comments(student_id):
    student = Student.query.get_or_404(student_id)
    comments = StudentComment.query.filter_by(student_id=student_id).order_by(StudentComment.created_at.desc()).all()
    return render_template("view_comments.html", student=student, comments=comments)

@admin_bp.route('/select-student-comments')
@login_required
def select_student_for_comments():
    students = Student.query.filter_by(status='active').all()
    return render_template('select_student_for_comments.html', students=students)


@admin_bp.route('/view-students')
@login_required
def view_students():
    students = Student.query.all()
    return render_template('student_list.html', students=students)



@admin_bp.route('/add-comment', methods=['POST'])
@login_required
def add_comment():
    from flask import jsonify

    data = request.get_json()
    student_id = data.get('student_id')
    comment_text = data.get('comment')

    if not student_id or not comment_text:
        return jsonify({'success': False, 'message': 'Missing data'}), 400

    try:
        comment = StudentComment(student_id=student_id, comment=comment_text)
        db.session.add(comment)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Comment saved'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500



from flask import request, redirect, url_for, flash
from forms.student_form import AddStudentForm

@admin_bp.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    form = AddStudentForm(obj=student)  # ✅ Prepopulate form

    if request.method == 'POST' and form.validate_on_submit():
        # Manually assign fields (skip .populate_obj)
        student.name = form.name.data
        student.residing_country = form.residing_country.data
        student.gender = form.gender.data
        student.email = form.email.data
        student.student_country_code = form.student_country_code.data
        student.phone = form.phone.data
        student.parent_name = form.parent_name.data
        student.parent_email = form.parent_email.data
        student.parent_country_code = form.parent_country_code.data
        student.parent_phone = form.parent_phone.data
        student.discord_id = form.discord_id.data
        student.sibling_reference = form.sibling_reference.data
        student.learning_subject = form.learning_subject.data
        student.fee_per_month = form.fee_per_month.data
        student.notes = form.notes.data

        # ✅ Fix these:
        student.classes_per_week = form.classes_per_week.data
        student.timezone = form.timezone.data

        # Optional: Do not update class_times for now
        # Future: Implement a proper method to update this relationship

        student.zoom_link = form.zoom_link.data
        student.zoom_password = form.zoom_password.data

        student.date_of_birth = form.date_of_birth.data
        student.grade = form.grade.data
        student.school_name = form.school_name.data
        student.hobbies = form.hobbies.data
        student.start_date = form.start_date.data
        student.end_date = form.end_date.data

        student.future_college = form.future_college.data
        student.future_stream = form.future_stream.data
        student.career_interest = form.career_interest.data

        db.session.commit()
        flash('Student details updated successfully.', 'success')
        return redirect(url_for('admin.student_list'))

    return render_template('edit_student.html', student=student, form=form)

