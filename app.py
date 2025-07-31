import smtplib
from datetime import datetime
from email.message import EmailMessage
from functools import wraps
from hashlib import md5
from os import environ, urandom
from urllib.parse import urlencode

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
from models import Comments, Post, User, db

# from flask_gravatar import Gravatar


load_dotenv('.env')

secret_key: bytes = urandom(32)

app: Flask = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db.init_app(app)
# Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
bootstrap = Bootstrap5(app)
crsf = CSRFProtect(app)
ckeditor = CKEditor(app)

# with app.app_context():
#     db.drop_all()
#     db.create_all()


year: int = datetime.now().year


def gravatar_url(email, size=100, default='retro', rating='g'):
    """Generate Gravatar URL"""

    email_hash = md5(email.lower().encode('utf-8')).hexdigest()
    params = urlencode({'d': default, 's': str(size), 'r': rating})

    return f"https://www.gravatar.com/avatar/{email_hash}?{params}"


app.jinja_env.globals.update(gravatar_url=gravatar_url)


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
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
        )
        user.set_password(form.confirm_password.data)

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

    return render_template('register.html',
                           form=form,
                           year=year,
                           whatsapp=environ.get('WHATSAPP'),
                           github=environ.get('GITHUB'))


@app.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        next_url = request.args.get('next') or url_for('home')
        return redirect(next_url)

    form = LoginUser()

    user: User | None = db.session.scalar(
        select(User).where(User.email == form.email.data))

    if user is None:
        flash('Do not have an account? Register an account for free', 'danger')
    else:
        if user.check_password(form.password.data):
            login_user(user, remember=True)
            flash(f'{user.username.split()[0]} has logged in!')
            next_url = request.args.get('next') or url_for('home')
            return redirect(next_url)
        else:
            flash('Invalid email or password!', category='error')

    return render_template('login.html',
                           form=form,
                           year=year,
                           whatsapp=environ.get('WHATSAPP'),
                           github=environ.get('GITHUB'))


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
                admin=admin,
                whatsapp=environ.get('WHATSAPP'),
                github=environ.get('GITHUB')
            )
        else:
            return render_template(
                'index.html',
                slice_blog_data=blog_data,
                year=year,
                admin=admin,
                whatsapp=environ.get('WHATSAPP'),
                github=environ.get('GITHUB'))
    else:
        return render_template(
            'index.html',
            year=year,
            admin=admin,
            whatsapp=environ.get('WHATSAPP'),
            github=environ.get('GITHUB'))


@app.route('/all-blogs')
def all_blogs():
    page: int = request.args.get('page', 1, type=int)
    blogs_per_page = db.paginate(
        select(Post).order_by(Post.date.desc()),
        page=page,
        per_page=15,
        error_out=False
    )

    next_page = url_for('all_blogs', page=blogs_per_page.next_num) \
        if blogs_per_page.has_next else None

    prev_page = url_for('all_blogs', page=blogs_per_page.prev_num) \
        if blogs_per_page.has_prev else None

    return render_template('allBlogs.html',
                           blogs=blogs_per_page.items,
                           next_page=next_page,
                           prev_page=prev_page,
                           year=year,
                           admin=db.session.get(User, 1),
                           whatsapp=environ.get('WHATSAPP'),
                           github=environ.get('GITHUB'))


@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
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

    username: str = post_to_disp.author.username.split(
    )[0] if post_to_disp.author else 'Unknown'

    date_composed = str(post_to_disp.date).split()[0]

    if comments_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Login to add comment!', category='danger')
            return redirect(url_for('login'))

        user_comment = Comments(
            comment=cleanify(comments_form.comment.data),
            the_user=current_user,
            blog_post=post_to_disp
        )
        db.session.add(user_comment)
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
        comments=comments,
        date_composed=date_composed,
        whatsapp=environ.get('WHATSAPP'),
        github=environ.get('GITHUB'))


@app.route('/add-post', methods=['POST', 'GET'])
@login_required
def add_post():
    form = CreatePost()

    if form.validate_on_submit():
        try:
            new_post = Post(
                title=form.title.data,
                subtitle=form.subtitle.data,
                body=cleanify(form.body.data),
                img_url=form.img_url.data or url_for(
                    'static', filename='assets/img/post-bg.jpg'),
                author=current_user
            )
            db.session.add(new_post)
            db.session.commit()

            added_post = db.session.get(Post, new_post.id)
            if not added_post:
                flash('Failed to verify post creation', category='error')
                return redirect(url_for('home'))

            flash('Successfullly added!', category='success')
            return redirect(url_for('home'))

        except IntegrityError:
            db.session.rollback()
            flash('Post with this title already exists', category='error')
        except Exception as e:
            db.session.rollback()
            flash('Failed to add post', category='error')
            app.logger.error(f'Error adding post: {str(e)}')

    return render_template('create-post.html',
                           form=form, year=year, current_user=current_user,
                           whatsapp=environ.get('WHATSAPP'),
                           github=environ.get('GITHUB'))


@app.route('/edit-post/<int:post_id>', methods=['POST', 'GET'])
@login_required
@admins_only
def edit_post(post_id: int):
    post_to_edit = db.session.get(Post, post_id)
    form = CreatePost()
    if not post_to_edit:
        flash('Post not available to edit!', category='danger')
        return redirect(url_for('home'))

    if form.validate_on_submit():
        try:
            db.session.execute(
                update(Post).where(Post.id == post_id).values(
                    title=form.title.data,
                    subtitle=form.subtitle.data,
                    body=cleanify(form.body.data),
                    img_url=form.img_url.data
                )
            )
            db.session.commit()
            flash('Post updated successfully!', category='success')
            return redirect(url_for('show_post'))

        except IntegrityError as ie:
            flash('Your new title is used by someone...Modify it!', 'danger')
            print(str(ie))
            db.session.rollback()
        except Exception as e:
            flash('Failed to update!', category='error')
            print(f'error: {str(e)}')
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
        post_title=post_title,
        whatsapp=environ.get('WHATSAPP'),
        github=environ.get('GITHUB'))


@app.route('/delete-post/<int:post_id>')
@login_required
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
    return render_template('about.html', year=year,
                           whatsapp=environ.get('WHATSAPP'),
                           github=environ.get('GITHUB'))


@app.route('/contact', methods=['POST', 'GET'])
@login_required
def contact_page():
    """
    """

    api_token: str = environ.get('API_TOKEN')
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

    return render_template('contact.html',
                           year=year, is_sent=False, api_token=api_token,
                           whatsapp=environ.get('WHATSAPP'),
                           github=environ.get('GITHUB'))


@app.route('/logging-out')
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
