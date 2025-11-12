from models import Comments, Post, User
from models import db as models_db


def test_user_password_and_relationship(app):
    with app.app_context():
        user = User(username='Test User', email='test.user@example.com')
        user.set_password('supersecurepassword')
        models_db.session.add(user)
        models_db.session.commit()

        assert user.check_password('supersecurepassword') is True
        assert user.id is not None

        post = Post(title='Title',
                    subtitle='Subtitle',
                    body='Body',
                    author=user)
        models_db.session.add(post)
        models_db.session.commit()

        # relationship check
        assert post.author.id == user.id
        assert post in user.posts.all()


def test_comments_link_to_post_and_user(app):
    with app.app_context():
        user = User(username='Commenter', email='commenter@example.com')
        user.set_password('commentersecurepassword')
        models_db.session.add(user)
        models_db.session.commit()

        post = Post(title='Post for comments',
                    subtitle='subtitle', body='body', author=user)
        models_db.session.add(post)
        models_db.session.commit()

        comment = Comments(comment='Nice post',
                           user_id=user.id, post_id=post.id)
        models_db.session.add(comment)
        models_db.session.commit()

        stored = models_db.session.get(Comments, comment.id)
        assert stored is not None
        assert stored.post_id == post.id
        assert stored.user_id == user.id
