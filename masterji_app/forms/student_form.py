from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Optional
from wtforms import SelectField


class AddStudentForm(FlaskForm):
    name = StringField('Student Name', validators=[DataRequired()])
    
    residing_country = SelectField('Residing Country', choices=[('', 'Choose'), ('India', 'India'), ('USA', 'USA'), ('UK', 'UK')])
    gender = SelectField('Gender', choices=[('', 'Choose'), ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    
    email = StringField('Student Email', validators=[Optional()])
    student_country_code = SelectField(
    'Country Code (Student)',
    choices=[('+1', 'USA (+1)'), ('+91', 'India (+91)'), ('+44', 'UK (+44)')],
    validators=[Optional()]
)
    phone = StringField('Student Phone', validators=[Optional()])
    
    parent_name = StringField('Parent Name', validators=[Optional()])
    parent_email = StringField('Parent Email', validators=[Optional()])
    parent_country_code = SelectField(
    'Country Code (Parent)',
    choices=[('+1', 'USA (+1)'), ('+91', 'India (+91)'), ('+44', 'UK (+44)')],
    validators=[Optional()]
)
    parent_phone = StringField('Parent Phone', validators=[Optional()])
    
    discord_id = StringField('Discord ID', validators=[Optional()])
    sibling_reference = StringField('Sibling/Friend', validators=[Optional()])
    learning_subject = StringField('Learning Subject', validators=[Optional()])
    fee_per_month = FloatField('Monthly Fee (USD)', validators=[DataRequired()])
    notes = TextAreaField('Comments / Notes', validators=[Optional()])
    
    submit = SubmitField('Add Student')
