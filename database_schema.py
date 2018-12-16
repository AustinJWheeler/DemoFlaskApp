from psycopg2._psycopg import Column
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, create_engine
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    email = Column(String, primary_key=True, nullable=False)
    password = Column(String)
    email_verification_token = Column(String, unique=True)


class UserSession(Base):
    __tablename__ = 'session'

    id = Column(String, primary_key=True)
    user_email = Column(String, ForeignKey('user.email'))
    init_time = Column(DateTime)
    login_exp_time = Column(DateTime)
    flash = Column(String)


class Category(Base):
    __tablename__ = 'category'

    name = Column(String, primary_key=True)


class Item(Base):
    __tablename__ = 'item'

    category = Column(String, ForeignKey('category.name'), primary_key=True)
    item = Column(String, primary_key=True)
    description = Column(String)
    user_email = Column(String, ForeignKey('user.email'))


engine = create_engine('sqlite:///database.db')


Base.metadata.create_all(engine)
