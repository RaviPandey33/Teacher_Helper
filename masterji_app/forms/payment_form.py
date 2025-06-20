from flask_wtf import FlaskForm
from wtforms.fields import DateField
from wtforms import SubmitField
from wtforms.validators import DataRequired

class MonthlyPaymentForm(FlaskForm):
    month = DateField('Select Month', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Update Payments')
