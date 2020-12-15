from flask import Flask, render_template, url_for, request, redirect, session, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, func

from hashlib import sha256
from datetime import datetime

import pandas as pd


app = Flask(__name__)
app.secret_key = 'secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///news.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)



class User(db.Model):
    __tablename__ = "users"
    id         = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    email      = db.Column(db.String(255), nullable=False, unique=True)
    password   = db.Column(db.Text,        nullable=False)
    first_name = db.Column(db.String(255), nullable=False)
    last_name  = db.Column(db.String(255))
    favorites  = db.relationship('Favourite', backref='users', lazy='dynamic')
    def __repr__(self):
        return f"<User::{self.id}>"


class Source(db.Model):
    __tablename__ = "sources"
    id   = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    articles = db.relationship('Article', backref='sources', lazy='dynamic')
    def __repr__(self):
        return f"<Source::{self.id}>"


class Category(db.Model):
    __tablename__ = "categories"
    id   = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    articles = db.relationship('Article', backref='categories', lazy='dynamic')
    def __repr__(self):
        return f"<Category::{self.id}>"


class Article(db.Model):
    __tablename__ = "articles"
    id          = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    source_id   = db.Column(db.Integer, db.ForeignKey('sources.id'),    nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    author      = db.Column(db.String(255))
    title       = db.Column(db.String(511), nullable=False)
    description = db.Column(db.Text)
    url         = db.Column(db.Text)
    urlToImage  = db.Column(db.Text)
    publishedAt = db.Column(db.DateTime,    default=datetime.utcnow)
    content     = db.Column(db.Text)
    favorites   = db.relationship('Favourite', backref='articles', lazy='dynamic')
    def __repr__(self):
        return f"<Article::{self.id}>"
    def as_dict(self):
        return {
            'id': self.id, 
            'source_id': self.source_id, 
            'category_id': self.category_id,
            'author': self.author,
            'title': self.title,
            'description': self.description,
            'url': self.url,
            'urlToImage': self.urlToImage,
            'publishedAt': self.publishedAt,
            'content': self.content
        }


class Favourite(db.Model):
    __tablename__ = "favourites"
    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'),    nullable=False)
    article_id  = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    def __repr__(self):
        return f"<Favourite | User::{self.user_id} | Article::{self.article_id}>"



# >>> Main, Categories, Search, Favorite pages

@app.route('/')
def index():
    if 'email' in session and 'password' in session:
        categories = Category.query.order_by(Category.name).all()
        user = User.query.filter_by(email=session['email']).first()
        articles = Article.query.order_by(Article.publishedAt.desc()).all()[:20]
        
        favourites = Favourite.query.filter_by(user_id=user.id).all()
        favourite_articles = []
        for favourite in favourites:
            favourite_articles.append(favourite.article_id)
        
        return render_template('main/article.html', categories=categories, articles=articles[:20], user=user, favourite_articles=favourite_articles)
    else:
        return redirect('/login')


@app.route('/c/<string:name>')
def category(name):
    if 'email' in session and 'password' in session:
        categories = Category.query.order_by(Category.name).all()
        user = User.query.filter_by(email=session['email']).first()
        category = Category.query.filter_by(name=name).first()
        if category is not None:
            articles = Article.query.filter_by(category_id=category.id).order_by(Article.publishedAt.desc()).all()
            
            favourites = Favourite.query.filter_by(user_id=user.id).all()
            favourite_articles = []
            for favourite in favourites:
                favourite_articles.append(favourite.article_id)
            
            return render_template('main/article.html', categories=categories, articles=articles[:20], user=user, favourite_articles=favourite_articles)
        else:
            errorHeader = 'Not Found This Category'
            errors = [f"Category: {name}, doesn't exists"]
            return render_template('error.html', errorHeader=errorHeader, errors=errors)
    else:
        return redirect('/login')


@app.route('/search', methods=['GET'])
def search():
    if 'email' in session and 'password' in session:
        q = request.args['q'].lower()
        q = q.replace("-", " ").split()
        categories = Category.query.order_by(Category.name).all()
        user = User.query.filter_by(email=session['email']).first()
        articles = Article.query.order_by(Article.publishedAt.desc()).all()
        
        favourites = Favourite.query.filter_by(user_id=user.id).all()
        favourite_articles = []
        for favourite in favourites:
            favourite_articles.append(favourite.article_id)
        
        search_articles = []
        for article in articles:
            txt = article.sources.name.lower()      +" "+\
                  article.categories.name.lower()   +" "+\
                  article.author.lower()            +" "+\
                  article.title.lower()             +" "+\
                  article.description.lower()       +" "+\
                  article.content.lower()
            n = 0
            for s in q:
                if s in txt: n += 1
            if len(q) == n:
                search_articles.append(article)
        return render_template('main/article.html', categories=categories, articles=search_articles[:20], user=user, favourite_articles=favourite_articles)
    else:
        return redirect('/login')
    

@app.route('/favorite')
def favorite():
    if 'email' in session and 'password' in session:
        categories = Category.query.order_by(Category.name).all()
        user = User.query.filter_by(email=session['email']).first()
        
        favourites = Favourite.query.filter_by(user_id=user.id).all()
        favourite_articles = []
        for favourite in favourites:
            favourite_articles.append(favourite.article_id)
        
        all_articles = Article.query.order_by(Article.publishedAt.desc()).all()
        articles = []
        for article in all_articles:
            if article.id in favourite_articles:
                articles.append(article)
        
        return render_template('main/article.html', categories=categories, articles=articles, user=user, favourite_articles=favourite_articles)
    else:
        return redirect('/login')
    

import recommendation as rec

@app.route('/recommendation')
def recommendation():
    if 'email' in session and 'password' in session:
        categories = Category.query.order_by(Category.name).all()
        
        articles = Article.query.order_by(Article.publishedAt.desc()).all()
        df = pd.DataFrame([article.as_dict() for article in articles])
        
        user = User.query.filter_by(email=session['email']).first()
        favourites = Favourite.query.filter_by(user_id=user.id).all()
        if len(favourites) != 0:
            favourite_articles = []
            for favourite in favourites:
                favourite_articles.append(favourite.article_id)

            recommended_articles = rec.get_recommendations(favourite_articles, df)
            articles = Article.query.filter(Article.id.in_(recommended_articles)).order_by(Article.publishedAt.desc()).all()

            return render_template('main/article.html', categories=categories, articles=articles, user=user, favourite_articles=favourite_articles)
        else:
            return render_template('main/article.html', categories=categories, user=user)
    else:
        return redirect('/login')


# >>> Register, Login, Logout

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        users = User(email=email, password=sha256(password.encode("UTF-8")).hexdigest(), first_name=first_name, last_name=last_name)
        try:
            db.session.add(users)
            db.session.commit()
            return redirect('/login')
        except Exception as err:
            if err.args[0] == '(sqlite3.IntegrityError) UNIQUE constraint failed: users.email':
                return render_template('main/register.html', errors=["Email already exists"])
            else:
                return render_template('main/register.html', errors=["Other problem"])
    else:
        categories = Category.query.order_by(Category.name).all()
        return render_template('main/register.html', categories=categories)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = sha256(request.form['password'].encode("UTF-8")).hexdigest()
        user = User.query.filter_by(email=email).first()
        if user is not None:
            if user.password == password:
                session['email'] = email
                session['password'] = password
                return redirect('/')
            else:
                return render_template('main/login.html', errors=['Password incorrect'])
        else:
            return render_template('main/login.html', errors=['User not exists'])
    else:
        categories = Category.query.order_by(Category.name).all()
        return render_template('main/login.html', categories=categories)
    

@app.route('/logout')
def logout():
    if 'email' in session:
        del session['email']
    if 'password' in session:
        del session['password']
    return redirect('/login')


# >>> Other

@app.route('/addstar', methods=['POST'])
def addstar():
    if request.method == 'POST':
        req = request.get_json()
        favourite = Favourite.query.filter_by(user_id=req['user_id'], article_id=req['article_id']).first()
        if favourite is None:
            favourite = Favourite(user_id=req['user_id'], article_id=req['article_id'])
            try:
                db.session.add(favourite)
                db.session.commit()
                res = make_response(jsonify({'message':"This mark has been added"}), 200)
                return res
            except Exception as err:
                res = make_response(jsonify({'message':"ERROR adding this mark"}), 400)
                return res
        else:
            res = make_response(jsonify({'message':"This mark already exists"}), 300)
            return res
    else:
        res = make_response(jsonify({'message':"not Post"}), 400)
        return res


@app.route('/removestar', methods=['POST'])
def removestar():
    if request.method == 'POST':
        req = request.get_json()
        favourite = Favourite.query.filter_by(user_id=req['user_id'], article_id=req['article_id']).first()
        if favourite is not None:
            try:
                db.session.delete(favourite)
                db.session.commit()
                res = make_response(jsonify({'message':"This mark has been removed"}), 200)
                return res
            except Exception as err:
                res = make_response(jsonify({'message':"ERROR removing this mark"}), 400)
                return res
        else:
            res = make_response(jsonify({'message':"This mark doesn't exist"}), 300)
            return res
    else:
        res = make_response(jsonify({'message':"not Post"}), 400)
        return res
    
    
from category.prediction import *

@app.route('/predict', methods=['POST'])
def category_prediction():
    if request.method == 'POST':
        req = request.get_json()
        category_name = predict_category(req['content'])
        category_id = Category.query.filter_by(name=category_name).first().id
        res = make_response(jsonify({'category': category_id}), 200)
        return res
    else:
        res = make_response(jsonify({'message':"not Post"}), 400)
        return res


# >>> Admin

@app.route('/admin/articles', methods=['POST', 'GET'])
def admin_article():
    if 'admin_email' in session and 'admin_password' in session:
        categories = Category.query.order_by(Category.name).all()
        if request.method == 'POST':
            source_name = request.form['source']
            category_id = request.form['category']
            author = request.form['author']
            title = request.form['title']
            description = request.form['description']
            url = request.form['url']
            urlToImage = request.form['urlToImage']
            content = request.form['content']
            
            source = Source.query.filter_by(name=source_name).first()
            if source is not None:
                source_id = source.id
            else:
                source = Source(name=source_name)
                try:
                    db.session.add(source)
                    db.session.commit()
                    source_id = source.id
                except Exception as err:
                    if err.args[0] == '(sqlite3.IntegrityError) UNIQUE constraint failed: sources.name':
                        return render_template('admin/article.html', categories=categories, errors=["Source already exists"])
                    else:
                        return render_template('admin/article.html', categories=categories, errors=["Other problem"])
            
            article = Article(
                source_id   = source_id,
                category_id = category_id,
                author      = author,
                title       = title,
                description = description,
                url         = url,
                urlToImage  = urlToImage,
                content     = content
            )
            try:
                db.session.add(article)
                db.session.commit()
                return redirect('/admin/articles')
            except Exception as err:
                return render_template('admin/article.html', categories=categories, errors=["Other problem"])
        else:
            return render_template('admin/article.html', categories=categories)
    else:
        return redirect('/admin/login')


@app.route('/admin')
@app.route('/admin/dashboard')
def admin_index():
    if 'admin_email' in session and 'admin_password' in session:
        users = User.query.all()
        sources = Source.query.all()
        categories = Category.query.all()
        articles = Article.query.all()
        categories_name__articles_number = []
        for category_id__article_number in Article.query.with_entities(Article.category_id, func.count(Article.id).label("number")).group_by(Article.category_id).order_by(desc("number")):
            categories_name__articles_number.append( {"name":Category.query.get(category_id__article_number[0]).name, "number":category_id__article_number[1]} )
        return render_template('admin/dashboard.html', users=users, sources=sources, categories=categories, articles=articles, categories_name__articles_number=categories_name__articles_number)
    else:
        return redirect('/admin/login')


@app.route('/admin/login', methods=['POST', 'GET'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = sha256(request.form['password'].encode("UTF-8")).hexdigest()
        if email == "admin@email.com" and password == sha256("admin".encode("UTF-8")).hexdigest():
            session['admin_email'] = email
            session['admin_password'] = password
            return redirect('/admin/dashboard')
        else:
            return render_template('admin/login.html', errors=['Admin or password incorrect'])
    else:
        return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    if 'admin_email' in session:
        del session['admin_email']
    if 'admin_password' in session:
        del session['admin_password']
    return redirect('/admin/login')



# >>> Run

if __name__=="__main__":
	app.run(debug=True)

