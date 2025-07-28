from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, StringField, SubmitField
from wtforms.validators import (DataRequired, Email, EqualTo, InputRequired,
                                Length)
from flask_ckeditor import CKEditorField


class CreatePost(FlaskForm):
    title = StringField(
        'Title', validators=[DataRequired(), Length(max=250)])
    subtitle = StringField(
        'Subtitle', validators=[DataRequired(), Length(max=250)])
    body = CKEditorField(
        'Body', validators=[DataRequired(), Length(max=1000)])
    img_url = StringField(
        'Image URL', validators=[Length(max=500)])
    add = SubmitField('Add Post')


class LoginUser(FlaskForm):
    email = EmailField('Email', validators=[
        Email(), DataRequired()])
    password = PasswordField('Password', validators=[
        DataRequired(), Length(max=50)])
    login = SubmitField('Sign In')


class SignUpUser(FlaskForm):
    username = StringField('Full name', validators=[
        InputRequired('Enter full name'),
        Length(max=250)])
    email = EmailField('Email', validators=[
        Email(), DataRequired()])
    password = PasswordField('Password', validators=[
        DataRequired(), Length(max=50)])
    confirm_password = PasswordField('Password', validators=[
        DataRequired(), Length(max=50), EqualTo('password', 'Wrong password!')
    ])
    create_account = SubmitField('Sign Up')
