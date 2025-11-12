from forms import CreatePost, LoginUser, SignUpUser, UsersComments


def test_signup_form_validation(app):
    with app.test_request_context():
        form = SignUpUser(
            username='Form Tester',
            email='form@example.com',
            password='pass1234',
            confirm_password='pass1234'
        )
        assert form.validate() is True


def test_login_form_validation(app):
    with app.test_request_context():
        form = LoginUser(email='f@example.com', password='pw')
        assert form.validate() is True


def test_create_post_form_validation(app):
    with app.test_request_context():
        form = CreatePost(title='Title', subtitle='Sub',
                          body='Body', img_url='')
        assert form.validate() is True


def test_users_comments_validation(app):
    with app.test_request_context():
        form = UsersComments(comment='Hi')
        assert form.validate() is True
