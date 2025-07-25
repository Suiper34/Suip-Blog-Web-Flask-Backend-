from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Text
from werkzeug.security import generate_password_hash, check_password_hash


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


class User(UserMixin, db.Model):
    __tablename__ = 'Users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(250))
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]

    def __repr__(self):
        return f'username: {self.username}, email:{self.email}, \
            password: {self.password}'

    def set_password(self, signup_password) -> str:
        return generate_password_hash(signup_password, salt_length=24)

    def check_password(self, login_password) -> bool:
        return check_password_hash(self.set_password, login_password)
