# Import library Flask
from flask import Flask, render_template, request, redirect, url_for, flash
from flask import jsonify, make_response

# Import library SQLAlchemy
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker

# Import library Database
from database_setup import Base, User, Category, CatalogItem

# Import to create a Login controller
from flask import session as login_session
import random
import string

# Import Library for OAuth
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"

# Initialize Flask
app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# JSON
@app.route('/catalog.json')
def showCatalogJSON():
    catalog = session.query(CatalogItem).all()
    return jsonify(catalog=[c.serialize for c in catalog])


# List all categories
@app.route('/')
@app.route('/catalog')
def showCategories():
    categories = session.query(Category).order_by(asc(Category.name))
    items = session.query(CatalogItem).order_by(desc(CatalogItem.id)).limit(10)
    return render_template('catalog.html', categories=categories, items=items,
                           login_session=login_session)


# login
@app.route('/login', methods=['GET', 'POST'])
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state

    if request.method == 'POST':
        user = session.query(User).filter_by(name=request.form['name']).first()
        if user is not None:
            if user.password == request.form['password']:
                connect_session(user)
                return redirect(url_for('showCategories'))
            else:
                flash('Password invalid!')
                return render_template('login.html', STATE=state)
        else:
            flash('User not found!')
            return render_template('login.html', STATE=state)
    else:
        return render_template('login.html', STATE=state)


# Get User ID by Email
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except ex:
        return None


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
        showLogin()


def createUserbyOAuth(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')

    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('User is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUserbyOAuth(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    return output


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('User not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token='
    url += '%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        disconnect()
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Connect Login  Session
def connect_session(user):
    login_session['user_id'] = user.id
    login_session['username'] = user.name
    login_session['email'] = user.email
    login_session['picture'] = user.picture


# Disconnect Login Session
@app.route('/disconnect')
def disconnect():
    if 'access_token' in login_session:
        del login_session['access_token']
    if 'gplus_id' in login_session:
        del login_session['gplus_id']
    del login_session['user_id']
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['state']
    return redirect(url_for('showCategories'))


# Create new Category
@app.route('/category/create', methods=['GET', 'POST'])
def createCategory():
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    if request.method == 'POST':
        category = Category(name=request.form['name'],
                            user_id=login_session['user_id'])
        session.add(category)
        session.commit()
        flash('Category included successfully')
        return redirect(url_for('showCategories'))
    else:
        return render_template('createcategory.html')


# Edit a Category
@app.route('/category/<string:category_name>/edit/', methods=['GET', 'POST'])
def editCategory(category_name):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    category = session.query(Category).filter_by(name=category_name).first()
    if category is not None:
        if request.method == 'POST':
            if request.form['name']:
                category.name = request.form['name']
            session.add(category)
            session.commit()
            flash('Category edited successfully')
        else:
            return render_template('editcategory.html',
                                   category_name=category_name)
    else:
        flash('Category not found, please Add the new category.')
    return redirect(url_for('showCategories'))


# Delete a Category
@app.route('/category/<string:category_name>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_name):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    category = session.query(Category).filter_by(name=category_name).first()
    if category is not None:
        if request.method == 'POST':
            session.delete(category)
            session.commit()
            flash('Category deleted successfully.')
        else:
            return render_template('deletecategory.html', category=category,
                                   login_session=login_session)
    else:
        flash('Category not found.')
    return redirect(url_for('showCategories'))


# List Items from a Category
@app.route('/catalog/<string:category_name>/items/')
def showCatalogItems(category_name):
    categories = session.query(Category).order_by(asc(Category.name))
    actualcategory = session.query(Category).filter_by(
        name=category_name).first()
    items = session.query(CatalogItem).filter_by(category_id=actualcategory.id)
    return render_template('catalogitem.html', categories=categories,
                           items=items, actualcategory=actualcategory,
                           login_session=login_session)


# Item Detail
@app.route('/catalog/<string:category_name>/<string:catalog_item>/')
def showCatalogItemDetail(category_name, catalog_item):
    item = session.query(CatalogItem).filter_by(title=catalog_item).first()
    if item is not None:
        return render_template('itemdetail.html', item=item,
                               login_session=login_session)
    else:
        flash('Item not Found.')
        return redirect(url_for('showCategories'))


# Create a new Catalog Item
@app.route('/catalog/create/', methods=['GET', 'POST'])
def createCatalogItem():
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    if request.method == 'POST':
        newitem = CatalogItem(title=request.form['title'],
                              description=request.form['description'],
                              category_id=request.form['category_id'],
                              user_id=login_session['user_id'])
        session.add(newitem)
        session.commit()
        flash('New Item created successfully.')
    else:
        categories = session.query(Category).all()
        return render_template('createitem.html',
                               categories=categories)
    return redirect(url_for('showCategories'))


# Edit a Catalog Item
@app.route('/catalog/<string:catalog_item>/edit/', methods=['GET', 'POST'])
def editCatalogItem(catalog_item):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    categories = session.query(Category).all()
    item = session.query(CatalogItem).filter_by(title=catalog_item).first()
    if item is not None:
        if request.method == 'POST':
            if request.form['title']:
                item.title = request.form['title']
            if request.form['description']:
                item.description = request.form['description']
            if request.form['category_id']:
                item.category_id = request.form['category_id']
            item.user_id = login_session['user_id']
            session.add(item)
            session.commit()
            flash('Item edited successfully.')
        else:
            return render_template('edititem.html',
                                   categories=categories, item=item)
    else:
        flash('Item not found.')
    return redirect(url_for('showCategories'))


# Delete a Catalog Item
@app.route('/catalog/<string:catalog_item>/delete/',
           methods=['GET', 'POST'])
def deleteCatalogItem(catalog_item):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    item = session.query(CatalogItem).filter_by(title=catalog_item).first()
    if item is not None:
        if request.method == 'POST':
            session.delete(item)
            session.commit()
            flash('Item deleted successfully.')
        else:
            return render_template('deleteitem.html', item=item,
                                   login_session=login_session)
    else:
        flash('Item not found.')
    return redirect(url_for('showCategories'))


if __name__ == '__main__':
    app.secret_key = 'udacity_project'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
