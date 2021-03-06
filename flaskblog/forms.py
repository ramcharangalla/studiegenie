from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField,SelectField,SelectMultipleField, TextAreaField, RadioField
from wtforms.validators import ValidationError,DataRequired, Length, Email, EqualTo
from flaskblog.models import User

my_choices = [('1', 'Java'), ('2', 'C++'), ('3', 'Python'),
            ('4', 'JavaScript'), ('5', 'Angular'), ('6', 'React'),
            ('7', 'MongoDB'), ('8', 'HTML'), ('9', 'CSS'),('10', 'Node.js')]


class RegistrationForm(FlaskForm):

    firstname = StringField('First Name', validators=[DataRequired(), Length(min=2, max=20)])
    lastname = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email ID', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',validators=[DataRequired(), EqualTo('password')])
    interests=SelectMultipleField('Interests', choices=my_choices, default = ['1'])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email ID already exists!!! Please go and Log IN')


class LoginForm(FlaskForm):
    email = StringField('Email ID',validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class NoteForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    interests=SelectMultipleField('Interests', choices=my_choices, default = ['1'])
    display_mode = RadioField('Mode', choices=[('public','Public'),('private','Private')])
    submit = SubmitField('Create Note')

class NoteFormUpdate(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    interests=SelectMultipleField('Interests', choices=my_choices, default = ['1'])
    display_mode = RadioField('Mode', choices=[('public','Public'),('private','Private')])
    submit = SubmitField('Update Note')

class LikeForm(FlaskForm):
    submitlike = SubmitField('Like')
    submitunlike = SubmitField('UnLike')
