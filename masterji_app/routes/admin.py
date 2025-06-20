from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.student import Student
from models.attendance import Attendance
from models.payment import Payment
from forms.student_form import AddStudentForm
from forms.attendance_form import AttendanceForm
from forms.payment_form import MonthlyPaymentForm
from datetime import date, datetime, timedelta
from forms.attendance_by_name_form import AttendanceByNameForm


admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('admin_dashboard.html', user=current_user)

@admin_bp.route('/add-student', methods=['GET', 'POST'])
@login_required
def add_student():
    form = AddStudentForm()
    if form.validate_on_submit():
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
            residing_country=form.residing_country.data
        )
        db.session.add(new_student)
        db.session.commit()
        flash('Student added successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('add_student.html', form=form)


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
                    record = Attendance(student_id=student.id, date=selected_date)
                    db.session.add(record)
                record.status = status
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
    student = Student.query.get_or_404(student_id)
    Attendance.query.filter_by(student_id=student.id).delete()
    Payment.query.filter_by(student_id=student.id).delete()
    db.session.delete(student)
    db.session.commit()
    flash(f"{student.name} has been permanently deleted.", "warning")
    return redirect(url_for('admin.student_list'))
