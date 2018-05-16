# SQLAlchemy
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine


Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    password = Column(String(250), nullable=False)
    picture = Column(String(250))


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship("User")
    items = relationship("CatalogItem", back_populates="category")
    # JSON objects in a serializable format
    @property
    def serialize(self):
        def serializeItem(item):
            return {
                'id': item.id,
                'title': item.title,
                'description': item.description,
            }
            
        def listItems(items):
            list = []
            for item in items:
                list.append(serializeItem(item))
            return list

        return {
            'id': self.id,
            'name': self.name,
            'items': listItems(self.items),
        }


class CatalogItem(Base):
    __tablename__ = 'catalogitem'

    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    description = Column(String(1000))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship("Category", back_populates="items")
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship("User")

    # JSON objects in a serializable format
    @property
    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
        }


engine = create_engine('sqlite:///catalog.db')
Base.metadata.create_all(engine)
