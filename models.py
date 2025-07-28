from datetime import datetime, timezone
from typing import List

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, \
    relationship, WriteOnlyMapped
from werkzeug.security import check_password_hash, generate_password_hash


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class Post(db.Model):
    __tablename__ = 'Posts'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True)
    subtitle: Mapped[str] = mapped_column(String(250))
    body: Mapped[str] = mapped_column(Text)
    # timezone utc to ensure uniform timestamps regardless of server location
    date: Mapped[datetime] = mapped_column(
        index=True,
        default=lambda: datetime.now(timezone.utc).strftime('%B %d, %Y')
        )
    img_url: Mapped[str | None] = mapped_column(String(500))
    author: Mapped['User'] = relationship(back_populates='posts')
    # foreign key uses tablename
    author_id: Mapped[int] = mapped_column(
        ForeignKey('user.id', ondelete='CASCADE'))

    all_comments: WriteOnlyMapped['Comments'] = relationship(
        backref='blog_post'
    )

    def __repr__(self):
        return f'username: {self.title}, email:{self.body}'


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(250))
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]

    posts: Mapped[List['Post']] = relationship(back_populates='author')
    # same as Mapped[List['Comments]]
    user_comments: WriteOnlyMapped['Comments'] = relationship(
        backref='the_user'
    )

    def __repr__(self):
        return f'username: {self.username}, email:{self.email}'

    def set_password(self, signup_password) -> str:
        return generate_password_hash(signup_password, salt_length=24)

    def check_password(self, login_password) -> bool:
        return check_password_hash(self.set_password, login_password)


class Comments(db.Model):
    __tablename__ = 'comments'

    id: Mapped[int] = mapped_column(primary_key=True)
    comment: Mapped[str] = mapped_column(Text)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('user.id', ondelete='CASCADE'))

    # use of backref in child class
    # the_user: Mapped['User'] = relationship(
    #     backref='comments', foreign_keys=[user_id], uselist=False)

    post_id: Mapped[str] = mapped_column(
        ForeignKey('blog_posts.id', ondelete='CASCADE'))

    def __repr__(self):
        return f'<comment: {self.comments}>'
