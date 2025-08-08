from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, TextAreaField, SelectField, SelectMultipleField, widgets, FieldList, FormField, DateField
from wtforms.validators import DataRequired, Optional
from datetime import date

# Multi-checkbox field for weekdays
class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

# Sub-form for each class time
class ClassTimeForm(FlaskForm):
    class Meta:
        csrf = False

    # Replace MultiCheckboxField with SelectField for a single day
    day = SelectField(
        'Class Day',
        choices=[
            ('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'),
            ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday'), ('Sunday', 'Sunday')
        ],
        validators=[Optional()]
    )
    hour = SelectField('Hour', choices=[(str(i), str(i)) for i in range(1, 13)], validators=[Optional()])
    minute = SelectField('Minute', choices=[(str(i).zfill(2), str(i).zfill(2)) for i in range(0, 60)], validators=[Optional()])
    am_pm = SelectField('AM/PM', choices=[('AM', 'AM'), ('PM', 'PM')], validators=[Optional()])


class AddStudentForm(FlaskForm):
    name = StringField('Student Name', validators=[DataRequired()])
    residing_country = SelectField('Residing Country', choices=[('', 'Choose'), ('India', 'India'), ('USA', 'USA'), ('UK', 'UK')])
    gender = SelectField('Gender', choices=[('', 'Choose'), ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    email = StringField('Student Email', validators=[Optional()])
    student_country_code = SelectField('Country Code (Student)', choices=[('+1', 'USA (+1)'), ('+91', 'India (+91)'), ('+44', 'UK (+44)')], validators=[Optional()])
    phone = StringField('Student Phone', validators=[Optional()])
    parent_name = StringField('Parent Name', validators=[Optional()])
    parent_email = StringField('Parent Email', validators=[Optional()])
    parent_country_code = SelectField('Country Code (Parent)', choices=[('+1', 'USA (+1)'), ('+91', 'India (+91)'), ('+44', 'UK (+44)')], validators=[Optional()])
    parent_phone = StringField('Parent Phone', validators=[Optional()])
    discord_id = StringField('Discord ID', validators=[Optional()])
    sibling_reference = StringField('Sibling/Friend', validators=[Optional()])
    learning_subject = StringField('Learning Subject', validators=[Optional()])
    fee_per_month = FloatField('Monthly Fee (USD)', validators=[DataRequired()])
    notes = TextAreaField('Comments / Notes', validators=[Optional()])

    # Class Details
    classes_per_week = SelectField('Number of classes per week', choices=[('1','1'),('2','2'),('3','3'),('4','4'),('5','5'),('6','6'),('7','7'),('Not Fix','Not Fix')], validators=[Optional()])
    timezone = SelectField('Time Zone', choices=[('PST', 'PST'), ('CST', 'CST'), ('EST', 'EST'), ('IST', 'IST')], validators=[Optional()])
    class_times = FieldList(FormField(ClassTimeForm), min_entries=5)# , max_entries=7)

    zoom_link = StringField('Zoom Link', validators=[Optional()])
    zoom_password = StringField('Zoom Password', validators=[Optional()])


    # Student Profile Details
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d', validators=[Optional()])
    grade = StringField('Current Grade/Class', validators=[Optional()])
    school_name = StringField('School Name', validators=[Optional()])
    hobbies = TextAreaField('Hobbies / Interests', validators=[Optional()])
    start_date = DateField('Start Date of Classes', format='%Y-%m-%d', validators=[Optional()])
    end_date = DateField('End Date of Classes (set automatically on inactivation)', format='%Y-%m-%d', validators=[Optional()])

    # Future Academic Tracking
    future_college = StringField('College Joined (If any)', validators=[Optional()])
    future_stream = StringField('College Stream / Major', validators=[Optional()])
    career_interest = TextAreaField('Career Interests / Goals', validators=[Optional()])

    submit = SubmitField('Add Student')
