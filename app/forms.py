from app import app
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DateTimeField, TextAreaField, RadioField, SelectField, IntegerField
from wtforms import validators, ValidationError
from wtforms.validators import DataRequired, Length, Email
from wtforms.fields.html5 import DateField
from wtforms_components import TimeField

class LoginForm(FlaskForm):
    device = SelectField('Select Device', choices = [('nsvpx1.realtracs.net','NSVPX1'),('nsvpx2.realtracs.net','NSVPX2')])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password',validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class OutageForm(FlaskForm):
    servicename = SelectField('Service', choices = [('.net', 'www.realtracs.net'), ('.com','www.realtracs.com'),('email','IceWarp Email')], validators=[DataRequired()])
    outagedate = DateField('Outage Date')
    outagestart = TimeField('Start Time')
    outagelength = IntegerField('Outage Length')
    outagecategory = RadioField('Category', choices = [('P','Planned'),('U','Unplanned')])
    outagereason = TextAreaField('Reason for outage', validators=[DataRequired(), Length(min=5, max=1024)])
    submit = SubmitField('Submit')

class ReportForm(FlaskForm):
    SelectedDate = DateField('Select Date for Report')
    submit = SubmitField('Generate Report')

class NSForm(FlaskForm):
    enablepvtflip = BooleanField('Enable Private Web Side Change')
    enablepubflip = BooleanField('Enable Public Web Side Change')
    enablebetaflip = BooleanField('Enable Beta Web Side Change')
    submit = SubmitField('Submit Changes')

class EmailReportForm(FlaskForm):
    selectedreport = RadioField('Which Report', choices=[('m', 'Monthly'), ('y','Yearly')])
    selecteddate = DateField('Select Date for Report')
    enteredemail = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Report')
