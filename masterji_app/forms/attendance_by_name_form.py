from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Optional

class AttendanceByNameForm(FlaskForm):
    student_query = StringField('Search', validators=[Optional()])
    submit = SubmitField('Search')
