# Import library SQLAlchemy
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker

# Import library Database
from database_setup import Base, User, Category, CatalogItem

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Get Lastest Itens
def getLastestItems(qtd):
    return session.query(CatalogItem).order_by(desc(CatalogItem.id)).limit(qtd)


# Get User by username
def getUserbyName(name):
    return session.query(User).filter_by(name=name).first()


# Get User by Email
def getUserbyEmail(email):
    user = session.query(User).filter_by(email=email).first()
    return user


# Get User by ID
def getUserbyID(id):
    user = session.query(User).filter_by(id=id).first()
    return user


# Create new User
def createUser(name, email, password):
    user = getUserbyName(name)
    if user is None:
        user = User(name=name, email=email, password=password)
        session.add(user)
        session.commit()
    return getUserbyName(name)


# Get All Categories
def getAllCategories():
    return session.query(Category).order_by(asc(Category.name))


def getCategorybyName(name):
    return session.query(Category).filter_by(name=name).first()


# Create new Category
def createCategory(name, user_id):
    category = Category(name=name, user_id=user_id)
    session.add(category)
    session.commit()
    return None


# Edit a Category
def editCategory(category, new_name):
    if new_name:
        category.name = new_name
        session.add(category)
        session.commit()
    return None


# Delete a Category
def deleteCategory(name):
    category = getCategorybyName(name)
    session.delete(category)
    session.commit()
    return None


# Get Items by Category ID
def getItemsbyCategoryID(id):
    return session.query(CatalogItem).filter_by(category_id=id)


# Get Item by ID
def getItemsbyID(id):
    return session.query(CatalogItem).filter_by(id=id)


# Get Item by Title
def getItemsbyTitle(title):
    return session.query(CatalogItem).filter_by(title=title).first()


# Create new CatalogItem
def createCatalogItem(title, description, category_id, user_id):
    newitem = CatalogItem(title=title, description=description,
                          category_id=category_id, user_id=user_id)
    session.add(newitem)
    session.commit()
    return None


# Edit a CatalogItem
def editCatalogItem(item, title, description, category_id, user_id):
    if title:
        item.title = title
    if description:
        item.description = description
    if category_id:
        item.category_id = category_id
    item.user_id = user_id
    session.add(item)
    session.commit()
    return None


# Delete a CatalogItem
def deleteCatalogItem(item):
    session.delete(item)
    session.commit()
    return None
