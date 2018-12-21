from sqlalchemy import Column, ForeignKey, String, DateTime, create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    email = Column(String, primary_key=True, nullable=False)


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

    @property
    def serialize(self):
        return {
            'name': self.name,
            'items': [i.serialize for i in self.items]
        }


class Item(Base):
    __tablename__ = 'item'

    category = Column(String, ForeignKey('category.name'), primary_key=True)
    category_object = relationship(Category, back_populates='items')
    item = Column(String, primary_key=True)
    description = Column(String)
    user_email = Column(String, ForeignKey('user.email'))

    @property
    def serialize(self):
        return {
            'category': self.category,
            'item': self.item,
            'description': self.description,
        }


Category.items = relationship("Item", order_by=Item.item,
                              back_populates="category_object")

engine = create_engine('sqlite:///database.db')
Base.metadata.create_all(engine)
