# login/register/upload forms
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, DateField, SelectField, FileField, SubmitField
from wtforms.validators import DataRequired, Email, Length, NumberRange, ValidationError
from datetime import datetime


class LoginForm(FlaskForm):
    """Login form for user authentication"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class RegisterForm(FlaskForm):
    """Registration form for new users"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Register')
    
    def validate_confirm_password(self, confirm_password):
        if self.password.data != confirm_password.data:
            raise ValidationError('Passwords do not match.')


class ExpenseForm(FlaskForm):
    """Form for adding/editing expenses"""
    description = StringField('Description', validators=[DataRequired(), Length(max=200)])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    category = SelectField('Category', choices=[
        ('Food', 'Food'),
        ('Transport', 'Transport'),
        ('Entertainment', 'Entertainment'),
        ('Rent', 'Rent'),
        ('Utilities', 'Utilities'),
        ('Shopping', 'Shopping'),
        ('Travel', 'Travel'),
        ('Health', 'Health'),
        ('Education', 'Education'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()], default=datetime.utcnow)
    submit = SubmitField('Add Expense')


class BudgetForm(FlaskForm):
    """Form for setting monthly budgets"""
    category = SelectField('Category', choices=[
        ('Food', 'Food'),
        ('Transport', 'Transport'),
        ('Entertainment', 'Entertainment'),
        ('Rent', 'Rent'),
        ('Utilities', 'Utilities'),
        ('Shopping', 'Shopping'),
        ('Travel', 'Travel'),
        ('Health', 'Health'),
        ('Education', 'Education'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    amount = FloatField('Monthly Budget', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Set Budget')


class UploadForm(FlaskForm):
    """Form for uploading CSV files"""
    file = FileField('CSV File', validators=[DataRequired()])
    submit = SubmitField('Upload CSV')
