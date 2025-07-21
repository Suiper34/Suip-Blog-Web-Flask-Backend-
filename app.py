from sqlalchemy import select, update, String, Text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from requests import get
import json
from datetime import datetime
from email.message import EmailMessage
import smtplib
from os import urandom, environ
from dotenv import load_dotenv

load_dotenv('.env')


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class Post(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True)
    subtitle: Mapped[str] = mapped_column(String(250))
    body: Mapped[str] = mapped_column(Text)
    date: Mapped[str] = mapped_column(String(250))
    author: Mapped[str] = mapped_column(String(250))


class CreatePostForm(FlaskForm):
    title = StringField(
        'title', validators=[DataRequired(), Length(max=250)])
    subtitle = StringField(
        'subtitle', validators=[DataRequired(), Length(max=250)])
    body = TextAreaField(
        'body', validators=[DataRequired(), Length(max=1000)])
    date = DateField(
        'date', validators=[DataRequired()], format='%B %d, %Y')
    author = StringField(
        'author', validators=[DataRequired(), Length(max=250)])
    add = SubmitField('Add Post')


secret_key: bytes = urandom(32)

app: Flask = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db.init_app(app)
bootstrap = Bootstrap5(app)
crsf = CSRFProtect(app)


with app.app_context():
    db.create_all()


def fetch_data():
    try:
        response = get('https://api.npoint.io/1e4f1e284ac8b96dac33')

    except (ConnectionError, Exception) as e:
        print('failed to fetch data', e)
        fetch_data()

    else:
        response.raise_for_status()
        data: json = response.json()
        return data


data = fetch_data()


with app.app_context():
    for post in data:
        db.session.add(Post(
            id=post.get('id'),
            title=post.get('title'),
            subtitle=post.get('subtitle'),
            body=post.get('body'),
            date=post.get('date'),
            author=post.get('author')
        ))
        db.session.commit()


year: int = datetime.now().year


@app.route('/')
def home():
    blog_data = db.session.execute(
        select(Post).order_by(Post.date)
    ).scalars().all()

    if blog_data:
        if len(blog_data) > 2:
            return render_template(
                'index.html',
                slice_blog_data=blog_data[:3],
                year=year,
            )
        else:
            return render_template(
                'index.html',
                slice_blog_data=blog_data,
                year=year,
            )


@app.route('/post/<int:post_id>')
def show_post(post_id: int):
    """
    Retrieve and display a blog post by its ID.
    """

    post_to_disp = db.session.get(Post, post_id)
    if not post_to_disp:
        flash('Post not found!', category='danger')
        return redirect(url_for('home'))

    return render_template('post.html', post=post_to_disp, year=year)


@app.route('/add-post', method=['POST', 'GET'])
def add_post():
    form = CreatePostForm()

    if form.validate_on_submit():
        try:
            db.session.add(Post(
                title=form.title.data,
                subtitle=form.subtitle.data,
                body=form.body.data,
                date=form.date.data,
                author=form.author.data
            ))
            db.session.commit()
            flash('Successfullly added!', category='success')
            return redirect(url_for('home'))

        except (IntegrityError, Exception) as e:
            print(e.detail)
            flash('Failed to add post', category='error')
            return redirect(url_for('home'))

    return render_template('create-post.html', form=form, year=year)


@app.route('/edit-post/<int:post_id>', methods=['POST', 'GET'])
def edit_post(post_id: int):
    return redirect(url_for('add_post'))


@app.route('/delete-post')
def delete_post():
    return redirect(url_for('home'))

@app.route('/about')
def about_page():
    return render_template('about.html', year=year)


@app.route('/contact', methods=['POST', 'GET'])
def contact_page():
    """
    If the request method is POST, retrieves form data (username, email, phone, message),
    logs in to a Gmail SMTP server using credentials from environment variables, and sends
    an email to the provided email address with the submitted message. Renders the contact
    page template with the current year in both GET and POST requests.
    """

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        with smtplib.SMTP_SSL('smtp.gmail.com') as mail_server:
            mail_server.login(user=environ.get('MAIL'),
                              password=environ.get('PASSWORD'))

            mail = EmailMessage()
            mail['From'] = environ.get('MAIL')
            mail['To'] = email
            mail['Subject'] = f'{username} , {phone}'
            mail.set_content(message)

            mail_server.send_message(mail)

        return render_template('contact.html', year=year, is_sent=True)

    return render_template('contact.html', year=year, is_sent=False)


if __name__ == '__main__':
    app.run(debug=True)
