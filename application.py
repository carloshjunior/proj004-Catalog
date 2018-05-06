# Import library Flask
from flask import Flask, render_template, request, redirect, url_for, flash
from flask import jsonify, make_response, session as login_session

# Import library SQLAlchemy
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker

# Import library Database
from database_setup import Base, User, Category, CatalogItem

# Initialize Flask
app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

categories = ['Football', 'Tennis', 'Basketball', 'Voleyball', 'Martial Arts']


# List all categories
@app.route('/')
@app.route('/Catalog')
def showCategories():
    # categories = session.query(Category).order_by(asc(Category.name))
    return render_template('categories.html', categories=categories,
                           login_session=login_session)


# login
@app.route('/login', methods=['GET', 'POST'])
def showLogin():
    if request.method == 'POST':
        user = session.query(User).filter_by(name=request.form['name']).first()
        if user is not None:
            if user.password == request.form['password']:
                connect_session(user)
                return redirect(url_for('showCategories'))
            else:
                flash('Password invalid!')
                return render_template('login.html')
            else:
                flash('User not found!')
                return render_template('login.html')
            else:
                return render_template('login.html')


# Create new User
@app.route('/createUser', methods=['GET', 'POST'])
def createUser():
    if request.method == 'POST':
        user = session.query(User).filter_by(name=request.form['name']).first()
        if user is not None:
            flash('User already exist.')
            return render_template('login.html')
        else:
            newUser = User(name=request.form['name'],
                           email=request.form['email'],
                           password=request.form['password'])
            session.add(newUser)
            session.commit()
            connect_session(newUser)
            return redirect(url_for('showCategories'))
        else:
            return render_template('login.html')


# Connect Login  Session
def connect_session(user):
    login_session['username'] = user.id
    login_session['email'] = user.email


# Disconnect Login Session
@app.route('/disconnect')
def disconnect():
    del login_session['username']
    del login_session['email']
    return redirect(url_for('showCategories'))


# Create new Category
@app.route('/category/create', methods=['GET', 'POST'])
def createCategory():
    return 'Create new Category'


# Edit a Category
@app.route('/category/<string:category_name>/edit/', methods=['GET', 'POST'])
def editCategory(category_name):
    return 'Edit a Category %s' % (category_name,)


# Delete a Category
@app.route('/category/<string:category_name>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_name):
    return 'Delete a Category %s' % (category_name,)


# List Items from a Category
@app.route('/catalog/<string:category_name>/items/')
def showCatalogItems(category_name):
    return 'Show all items of category %s' % (category_name,)


# Item Detail
@app.route('/catalog/<string:category_name>/<string:catalog_item>')
def showCatalogItemDetail(category_name, catalog_item):
    return 'Show detail about CatalogItem %s (%s)' % (category_name,
                                                      catalog_item,)


# Create a new Catalog Item
@app.route('/catalog/create/')
def createCatalogItem():
    return 'Create new CatalogItem'


# Edit a Catalog Item
@app.route('/catalog/<string:category_name>/<string:catalog_item>/edit/')
def editCatalogItem(category_name, catalog_item):
    return 'Edit CatalogItem %s (%s)' % (category_name, catalog_item,)


# Delete a Catalog Item
@app.route('/catalog/<string:category_name>/<string:catalog_item>/delete/')
def deleteCatalogItem(category_name, catalog_item):
    return 'Delete CatalogItem %s (%s)' % (category_name, catalog_item,)


if __name__ == '__main__':
    app.secret_key = 'udacity_project'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
