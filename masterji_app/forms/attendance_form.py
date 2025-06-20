from flask_wtf import FlaskForm
from datetime import date
from wtforms import DateField, SelectField, HiddenField, SubmitField
from wtforms.validators import DataRequired

class AttendanceForm(FlaskForm):
    date = DateField('Date', default=date.today, validators=[DataRequired()], format='%Y-%m-%d')
    submit = SubmitField('Save Attendance')

class AttendanceForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()])
    submit = SubmitField('Save Attendance')
