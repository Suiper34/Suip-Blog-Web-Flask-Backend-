import smtplib
from datetime import datetime
from email.message import EmailMessage
from functools import wraps
from os import environ, urandom

from dotenv import load_dotenv
from flask import (Flask, abort, flash, redirect, render_template, request,
                   url_for)
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
# santize user input before saving to db
from flask_ckeditor.utils import cleanify
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user)
# from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from forms import CreatePost, LoginUser, SignUpUser, UsersComments
from models import Post, User, db, Comments

load_dotenv('.env')

secret_key: bytes = urandom(32)

app: Flask = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blogposts.db'
db.init_app(app)
# Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
bootstrap = Bootstrap5(app)
crsf = CSRFProtect(app)
ckeditor = CKEditor(app)


with app.app_context():
    db.create_all()


year: int = datetime.now().year


# helper
def admins_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        admin: User | None = db.session.get(User, 1)
        if admin is None:
            flash('Admins only!', category='danger')
            return abort(403)
        if not admin:
            flash('Admins only!', category='danger')
            return abort(403)

        return func(*args, **kwargs)
    return wrapper


@login_manager.user_loader
def load_user(user_id):
    """
    Retrieves user by ID for session management.
    """
    return db.session.get(User, int(user_id))


@app.route('/register-user', methods=['POST', 'GET'])
def register_user():
    if current_user.is_authenticated:
        next_url = request.args.get('next')
        return redirect(next_url or url_for('home'))

    form = SignUpUser()
    user = User(
        username=form.username.data,
        email=form.email.data,
    )
    user.password = user.set_password(form.confirm_password.data)

    try:
        db.session.add(user)
        db.session.commit()
        flash('Account registered successfully!', category='success')
        next_url = url_for('login')
        return redirect(next_url)
    except IntegrityError:
        flash('Account already exist!\n\nUse different email', 'error')
    except Exception:
        flash('Failed to add account!', category='danger')
        db.session.rollback()

    return render_template('register.html', form=form)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        next_url = request.args.get('next') or url_for('home')
        return redirect(next_url)

    form = LoginUser()

    user: User | None = db.session.scalar(
        select(User).where(User.email == form.email.data))

    if user is None:
        flash('Account not exist!\n\nRegister an account for free', 'danger')
    else:
        if user.check_password(form.password.data):
            login_user(user, remember=True)
            flash(f'{user.username.split()[0]} has logged in!')
            next_url = request.args.get('next') or url_for('home')
            return redirect(next_url)
        else:
            flash('Invalid email or password!', category='error')

    return render_template('login.html', form=form)


@app.route('/')
def home():
    admin: User | None = db.session.get(User, 1)
    blog_data = db.session.execute(
        select(Post).order_by(Post.date.desc())
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
                admin=admin)


@app.route('/post/<int:post_id>')
def show_post(post_id: int):
    """
    Retrieve and display a blog post by its ID.
    """

    admin = db.session.get(User, 1)

    comments_form = UsersComments()

    post_to_disp = db.session.get(Post, post_id)
    if not post_to_disp:
        flash('Post not found!', category='danger')
        return redirect(url_for('home'))

    username: str = post_to_disp.author.username.strip(
    )[0] if post_to_disp.author else 'Unknown'

    if comments_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Login to add comment!', category='danger')
            return redirect(url_for('login'))

        db.session.add(Comments(
            comment=cleanify(comments_form.comment.data),
            the_user=current_user,
            blog_post=post_to_disp
        ))
        db.session.commit()

    comments = db.session.scalars(
        select(Comments).where(Comments.post_id == post_id)).all()

    return render_template(
        'post.html',
        post=post_to_disp,
        year=year,
        admin=admin,
        username=username,
        form=comments_form,
        comments=comments)


@app.route('/add-post', methods=['POST', 'GET'])
@login_required
def add_post():
    form = CreatePost()

    if form.validate_on_submit():
        try:
            db.session.add(Post(
                title=form.title.data,
                subtitle=form.subtitle.data,
                body=cleanify(form.body.data),
                img_url=form.img_url.data or url_for(
                    'static', filename='assets/img/post-bg.jpg'),
                author=current_user
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
@login_required
@admins_only
def edit_post(post_id: int):
    post_to_edit = db.session.get(Post, post_id)
    form = CreatePost()
    if not post_to_edit:
        flash('Post not available to edit!', category='danger')
        return redirect(url_for('show_post'))

    if form.validate_on_submit():
        try:
            db.session.execute(
                update(post_to_edit).values(
                    title=form.title.data,
                    subtitle=form.subtitle.data,
                    body=cleanify(form.body.data),
                    img_url=form.img_url.data
                )
            )
            db.session.commit()
            flash('Post updated successfully!', category='success')
            return redirect(url_for('show_post'))

        except Exception:
            flash('Failed to update!', category='error')
            print(f'error: {Exception}')
            db.session.rollback()

    form.title.data = post_to_edit.title
    form.subtitle.data = post_to_edit.subtitle
    form.body.data = post_to_edit.body
    form.img_url.data = post_to_edit.img_url

    post_title = post_to_edit.title
    return render_template(
        'create-post.html',
        form=form, year=year,
        is_existing=True,
        post_title=post_title)


@app.route('/delete-post/<int:post_id>')
@login_required()
@admins_only
def delete_post(post_id: int):
    post_to_delete = db.session.get(Post, post_id)

    if not post_to_delete:
        flash('Post not exist!', category='danger')
        return redirect(url_for('home'))

    try:
        db.session.delete(post_to_delete)
        db.session.commit()
        flash('Post deleted!', category='success')
    except Exception as e:
        flash('Failed to delete!', category='error')
        print(f'error: {e}')
        db.session.rollback()

    return redirect(url_for('home'))


@app.route('/about')
def about_page():
    return render_template('about.html', year=year)


@app.route('/contact', methods=['POST', 'GET'])
@login_required
def contact_page():
    """
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


@app.route('/logging-out')
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
