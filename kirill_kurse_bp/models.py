# models.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

db = SQLAlchemy()

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    
class User(db.Model):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), unique=True, nullable=False)
	email = db.Column(db.String(120), unique=True, nullable=False)
	password = db.Column(db.String(120), nullable=False)
	id_role = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
	role = db.relationship('Role', backref=db.backref('users', lazy=True))
	
	def get_current_role(self): # Возвращает текущую роль пользователя
		return self.role.name if self.role else None

	def is_guest(self): # Проверяет, является ли пользователь гостём
		return self.role and self.role.name == 'guest'

	def __repr__(self):
		return '<User %r>' % self.username

class Book(db.Model):
	__tablename__ = 'books'
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(64), unique=True, nullable=False)
	description = db.Column(db.Text, nullable=False)
	date = db.Column(db.Date, nullable=False)
	pages = db.Column(db.Integer, nullable=False)
	price = db.Column(db.Float, nullable=False)
	photo = db.Column(db.String(255), nullable=True)
	id_author = db.Column(db.Integer, db.ForeignKey('authors.id'), nullable=True)
	author = db.relationship('Author', backref=db.backref('books', lazy=True))
	id_genre = db.Column(db.Integer, db.ForeignKey('genres.id'), nullable=True)
	genre = relationship('Genre', backref=db.backref('genre_books', lazy=True))


class Author(db.Model):
    __tablename__ = 'authors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))

class Genre(db.Model):
    __tablename__ = 'genres'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=False)

class GenreBook(db.Model):
    __tablename__ = 'genre_books'
    id = db.Column(db.Integer, primary_key=True)
    id_book = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=True)
    id_genre = db.Column(db.Integer, db.ForeignKey('genres.id'), nullable=True)
    book = relationship('Book', backref=db.backref('genres', lazy=True))
    genre = relationship('Genre', backref=db.backref('books', lazy=True))

class Group(db.Model):
	__tablename__ = 'groups'
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(64), nullable=False)
	id_book = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=True)
	book = relationship('Book', backref=db.backref('groups', lazy=True))
     
class Comment(db.Model):
	__tablename__ = 'comments'
	id = db.Column(db.Integer, primary_key=True)
	text = db.Column(db.Text, nullable=False)
	date = db.Column(db.Date, nullable=False)
	id_user = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
	id_book = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=True)
	user = relationship('User', backref=db.backref('comments', lazy=True))
	book = relationship('Book', backref=db.backref('comments', lazy=True))
     
class Rating(db.Model):
	__tablename__ = 'ratings'
	id = db.Column(db.Integer, primary_key=True)
	rating = db.Column(db.Integer, nullable=False)
	id_user = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
	id_book = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=True)
	user = relationship('User', backref=db.backref('ratings', lazy=True))
	book = relationship('Book', backref=db.backref('ratings', lazy=True))

class Cart(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('carts', lazy=True))

class CartItem(db.Model):
    __tablename__ = 'cart_item'
    id = db.Column(db.Integer, primary_key=True)
    id_cart = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=True)
    id_book = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=True)
    quantity = db.Column(db.Integer, default=1)
    cart = db.relationship('Cart', backref=db.backref('items', lazy=True))
    book = db.relationship('Book', backref=db.backref('cart_items', lazy=True))
