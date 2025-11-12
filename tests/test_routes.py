from werkzeug.datastructures import MultiDict

from models import Post, User
from models import db as models_db


def create_user_and_post(app):
    with app.app_context():
        user = User(username='RouteTester', email='route@example.com')
        user.set_password('securepassword')
        models_db.session.add(user)
        models_db.session.commit()

        post = Post(title='Route Post', subtitle='Route Subtitle',
                    body='Route Body', author=user)
        models_db.session.add(post)
        models_db.session.commit()

        return user, post


def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'<header' in response.data or b'SUIP' in response.data or \
        b'Suip' in response.data


def test_show_post(client, app):
    user, post = create_user_and_post(app)
    response = client.get(f'/post/{post.id}')
    assert response.status_code == 200
    assert b'Route Post' in response.data or \
        post.title.encode() in response.data


def test_register_and_login_flow(client, app):
    # register
    reg_data = MultiDict({
        'username': 'New User',
        'email': 'new@example.com',
        'password': 'password1',
        'confirm_password': 'password1',
        'create_account': 'Sign Up'
    })
    response = client.post('/register-user',
                           data=reg_data,
                           follow_redirects=True)
    assert response.status_code in (200, 302)

    # login
    login_data = MultiDict({
        'email': 'new@example.com',
        'password': 'password1',
        'login': 'Sign In'
    })
    res2 = client.post('/login', data=login_data, follow_redirects=True)

    # after successful login, should reach a page (200) or redirect -> 200
    assert res2.status_code == 200
