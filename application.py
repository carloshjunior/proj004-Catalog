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


# List all categories
@app.route('/')
@app.route('/catalog')
def showCategories():
    categories = session.query(Category).order_by(asc(Category.name))
    items = session.query(CatalogItem).all()
    return render_template('catalog.html', categories=categories, items=items,
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
            user = User(name=request.form['name'],
                        email=request.form['email'],
                        password=request.form['password'])
            session.add(user)
            session.commit()
            user = session.query(User).filter_by(request.form['name']).first()
            connect_session(user)
            return redirect(url_for('showCategories'))
    else:
        return render_template('login.html')


# Connect Login  Session
def connect_session(user):
    login_session['id'] = user.id
    login_session['username'] = user.name
    login_session['email'] = user.email


# Disconnect Login Session
@app.route('/disconnect')
def disconnect():
    del login_session['id']
    del login_session['username']
    del login_session['email']
    return redirect(url_for('showCategories'))


# Create new Category
@app.route('/category/create', methods=['GET', 'POST'])
def createCategory():
    if request.method == 'POST':
        category = Category(name=request.form['name'],
                            user_id=login_session['id'])
        session.add(category)
        session.commit()
        flash('Category included successfully')
        return redirect(url_for('showCategories'))
    else:
        return render_template('createcategory.html')


# Edit a Category
@app.route('/category/<string:category_name>/edit/', methods=['GET', 'POST'])
def editCategory(category_name):
    category = session.query(Category).filter_by(name=category_name).first()
    if category is not None:
        if request.method == 'POST':
            category.name = request.form['name']
            session.add(category)
            session.commit()
            flash('Category edited successfully')
            return redirect(url_for('showCategories'))
        else:
            return render_template('editcategory.html',
                                   category_name=category_name)
    else:
        flash('Category not found, please Add the new category.')
        return redirect(url_for('createCategory'))


# Delete a Category
@app.route('/category/<string:category_name>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_name):
    return 'Delete a Category %s' % (category_name,)


# List Items from a Category
@app.route('/catalog/<string:category_name>/items/')
def showCatalogItems(category_name):
    return 'Show all items of category %s' % (category_name,)


# Item Detail
@app.route('/catalog/<string:category_name>/<string:catalog_item>/')
def showCatalogItemDetail(category_name, catalog_item):
    item = session.query(CatalogItem).filter_by(title=catalog_item).first()
    return render_template('itemdetail.html', item=item,
                           login_session=login_session)


# Create a new Catalog Item
@app.route('/catalog/create/', methods=['GET', 'POST'])
def createCatalogItem():
    if 'id' in login_session:
        if request.method == 'POST':
            newitem = CatalogItem(title=request.form['title'],
                                  description=request.form['description'],
                                  category_id=request.form['category_id'],
                                  user_id=login_session['id'])
            session.add(newitem)
            session.commit()
            flash('New Item created successfully.')
            return redirect(url_for('showCategories'))
        else:
            categories = session.query(Category).all()
            return render_template('createitem.html',
                                   categories=categories)
    else:
        flash("Access denied %s." % url_for('createCatalogItem'))
        return redirect(url_for('showCategories'))


# Edit a Catalog Item
@app.route('/catalog/<string:catalog_item>/edit/', methods=['GET', 'POST'])
def editCatalogItem(catalog_item):
    categories = session.query(Category).all()
    item = session.query(CatalogItem).filter_by(title=catalog_item).first()
    if 'id' in login_session:
        if request.method == 'POST':
            item = session.query(CatalogItem).filter_by(
                title=catalog_item).one()
            item.title = request.form['title']
            item.description = request.form['description']
            item.category_id = request.form['category_id']
            item.user_id = login_session['id']
            session.add(item)
            session.commit()
            flash('Item edited successfully.')
            return redirect(url_for('showCategories'))
        else:
            return render_template('edititem.html',
                                   categories=categories, item=item)
    else:
        flash('Access denied.')
        return redirect('showCategories')


# Delete a Catalog Item
@app.route('/catalog/<string:catalog_item>/delete/',
           methods=['GET', 'POST'])
def deleteCatalogItem(catalog_item):
    item = session.query(CatalogItem).filter_by(title=catalog_item).first()
    if request.method == 'POST':
        if 'id' in login_session:
            session.delete(item)
            session.commit()
            flash('Item deleted successfully.')
            return redirect(url_for('showCategories'))
    else:
        return render_template('deleteitem.html', item=item,
                               login_session=login_session)


if __name__ == '__main__':
    app.secret_key = 'udacity_project'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
