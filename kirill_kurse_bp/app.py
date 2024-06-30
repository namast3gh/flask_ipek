from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, text, delete
from sqlalchemy.sql.expression import func
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user, AnonymousUserMixin
from flask_migrate import Migrate
from flask_admin import Admin
import pandas as pd
from werkzeug.utils import secure_filename
import os
from flask_admin.contrib.sqla import ModelView  # Операции Create, Read, Update, Delete в веб -п приложении
from models import db, User, Role, Book, Author, Genre, GenreBook, Group, Comment, Rating, Cart, CartItem   # Предполагается, что здесь определены ваши модели
from datetime import datetime, timezone
import logging
from flask_mail import Mail, Message

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1232@localhost/library'


app.config['SECRET_KEY'] = 'dp[]kl2-pik-013k2kde2]1od0-12k-p2[lz[p12ek-01zi2z'


app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}


app.config['MAIL_SERVER'] = 'smtp.mail.ru'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'genger1356@mail.ru'
app.config['MAIL_PASSWORD'] = 'JRjVai0KyJuKuZ0C4wcx'

mail = Mail(app)


class Controller(ModelView):
    def is_accessible(self):
        if current_user.id_role == 1:
            return current_user.is_authenticated
        else:
            return abort(404)

    def not_auth(self):
        return "Вы не авторизованы"
    
    def can_delete(self, obj):
        return current_user.id_role == 1



login_manager = LoginManager(app)
login_manager.login_view = 'login'

db.init_app(app)
migrate = Migrate(app, db)

@app.before_request
def create_tables():
    with app.app_context():
        db.create_all()


# Присвоение роли "guest" всем неавторизованным пользователям
@app.before_request
def set_guest_role_if_not_logged_in():
    if not current_user.is_authenticated:
        guest_role = db.session.get(Role, 3)  # Получаем объект роли "guest"
        current_user.role = guest_role  # Присваиваем роль "guest" текущему пользователю
        db.session.commit()



@login_manager.user_loader
def load_user(user_id):
    # Загрузка пользователя по его ID, который является первичным ключом в таблице пользователей
    return db.session.get(Users, int(user_id))
	


class Users(db.Model, UserMixin):
    def get_id(self):
        # Возвращаем уникальный идентификатор пользователя
        return str(self.id)

    def is_active(self):
        return True

    def is_authenticated(self):
        return True


@app.route('/create_admin', methods=['GET', 'POST'])
@login_required
def create_admin():
    if current_user.id_role != 1:  # Проверяем, является ли текущий пользователь администратором
        return abort(404)

    if request.method == 'POST':
        new_user = Users(email=request.form['email'], password=request.form['password'], id_role=1)
        db.session.add(new_user)
        db.session.commit()
        flash('Администратор успешно создан.', 'success')
        return redirect(url_for('admin.index'))  # Перенаправляем на страницу администратора после успешного создания
    else:
        return render_template('admin_signup.html')


@app.route('/admin_users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.id_role!= 1:
        return abort(403)  # Запрещено удаление для пользователей, не являющихся администраторами

    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'Пользователь успешно удален'})
    else:
        return jsonify({'error': 'Пользователь не найден'}), 404

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        terms_agreed = 'terms_agreement' in request.form and request.form['terms_agreement'] == 'on'
        if not terms_agreed:
            flash('Вы должны согласиться с пользовательским соглашением, чтобы зарегистрироваться.', 'error')
            return render_template('register.html', title='Регистрация')

        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']  # Получаем подтверждение пароля

        if password!= confirm_password:
            flash('Пароли не совпадают. Пожалуйста, введите их еще раз.', 'error')
            return render_template('register.html', title='Регистрация')

        existing_user = Users.query.filter_by(email=email).first()
        if existing_user:
            print("Email уже зарегистрирован")
            flash('Пользователь с этим адресом электронной почты уже зарегистрирован.', 'error')
            return render_template('register.html', title='Регистрация')

        existing_username = Users.query.filter_by(username=username).first()
        if existing_username:
            print("Имя пользователя уже используется")
            flash('Это имя пользователя уже используется. Попробуйте другое.', 'error')
            return render_template('register.html', title='Регистрация')

        try:
            u = Users(username=username, email=email, password=password, id_role=2)
            db.session.add(u)
            db.session.commit()
            flash('Успешная регистрация Теперь вы можете войти в систему.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            print(f'Ошибка добавления в БД: {e}')
            flash('Произошла ошибка при регистрации. Пожалуйста, попробуйте снова.', 'error')
            return render_template('register.html', title='Регистрация')

    return render_template('register.html', title='Регистрация')


@app.route('/admin_table', methods=['GET', 'POST'])
@login_required
def admin_table():
    users = User.query.all()
    roles = Role.query.all() # получите все роли
    if request.method == 'POST':
        # Получите данные формы
        user_id = int(request.form.get('user_id'))
        user = User.query.get(user_id)
        if user:
            user.email = request.form.get('email')
            user.id_role = int(request.form.get('id_role'))
            db.session.commit()
    return render_template('admin_panel/admin_table.html', users=users, roles=roles)


@app.route('/admin_books', methods=['GET', 'POST'])
@login_required
def admin_books():
    if request.method == 'POST':
        try:
            new_title = request.form['title']
            new_description = request.form['description']
            new_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            new_pages = int(request.form['pages'])
            new_price = float(request.form['price'])
            genre_id = request.form['genre_id']
            new_photo = request.files.get('photo')

            if not genre_id:
                return jsonify({'error': 'Необходимо выбрать жанр.'}), 400

            if new_photo:
                filename = secure_filename(new_photo.filename)
                filepath = os.path.join('static/uploads/', filename)
                new_photo.save(filepath)
                image_url = '/static/uploads/' + filename
            else:
                image_url = None

            new_author_id = int(request.form['author_id'])
            new_book = Book(title=new_title, description=new_description, date=new_date, pages=new_pages, price=new_price, photo=image_url, id_author=new_author_id, id_genre=genre_id)
            db.session.add(new_book)
            db.session.commit()
            return jsonify({'message': 'Книга успешно добавлена'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    books = Book.query.all()
    authors = Author.query.all()
    genres = Genre.query.all()
    return render_template('admin_panel/admin_books.html', books=books, authors=authors,  genres=genres)

@app.route('/edit_book/<int:book_id>', methods=['GET'])
@login_required
def edit_book(book_id):
    book = db.session.get(Book, book_id)
    authors = Author.query.all()
    genres = Genre.query.all()
    if not book:
        return "Книга не найдена", 404
    return render_template('admin_panel/edit_book_form.html', book=book, authors=authors, genres=genres)

@app.route('/delete_book/<int:book_id>', methods=['DELETE'])
@login_required
def delete_book(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return "Книга не найдена", 404
    db.session.delete(book)
    db.session.commit()
    return "", 204

@app.route('/update_book/<int:book_id>', methods=['POST'])
@login_required
def update_book(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return "Книга не найдена", 404
    
    book.title = request.form['title']
    book.description = request.form['description']
    book.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()  # Преобразование строки даты в объект Date
    book.pages = int(request.form['pages'])
    book.price = float(request.form['price'])
    
    # Получение ID жанра и автора из формы
    genre_id = request.form['genre']
    author_id = request.form['author']
    
    # Обновление связей с жанром и автором
    book.id_genre = genre_id
    book.id_author = author_id
    
    # Загрузка нового фото
    if 'photo' in request.files:
        file = request.files['photo']
        filename = secure_filename(file.filename)
        filepath = os.path.join('static/uploads/', filename)
        file.save(filepath)
        book.photo = '/static/uploads/' + filename
    
    db.session.commit()
    return redirect(url_for('admin_books'))

@app.route('/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    authors = Author.query.all()
    genres = Genre.query.all()

    if request.method == 'POST':
        try:
            new_title = request.form['title']
            new_description = request.form['description']
            new_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            new_pages = int(request.form['pages'])
            new_price = float(request.form['price'])
            genre_id = request.form['genre']
            new_photo = request.files.get('photo')

            if not genre_id:
                return jsonify({'error': 'Необходимо выбрать жанр.'}), 400
            
            if new_photo:
                filename = secure_filename(new_photo.filename)
                filepath = os.path.join('static/uploads/', filename)
                new_photo.save(filepath)
                image_url = '/static/uploads/' + filename
            else:
                image_url = None
            
            new_author_id = int(request.form['author'])
            new_book = Book(title=new_title, description=new_description, date=new_date, pages=new_pages, price=new_price, photo=image_url, id_author=new_author_id, id_genre=genre_id)
            db.session.add(new_book)
            db.session.commit()
            return jsonify({'message': 'Книга успешно добавлена'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    return render_template('admin_panel/add_book_form.html', authors=authors, genres=genres)


@app.route('/admin/comments', methods=['GET', 'POST'])
@login_required
def admin_comments():
    comments = Comment.query.all()
    return render_template('admin_panel/admin_comments.html', comments=comments)

@app.route('/delete_comment/<int:comment_id>')
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    return redirect(url_for('admin_comments'))

@app.route('/edit_comment/<int:comment_id>', methods=['GET', 'POST'])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if request.method == 'POST':
        comment.text = request.form['text']
        db.session.commit()
        return redirect(url_for('admin_comments'))
    return render_template('admin_panel/edit_comment.html', comment=comment)


@app.route('/admin_genres')
@login_required
def admin_genres():
    genres = Genre.query.all()
    return render_template('admin_panel/admin_genres.html', genres=genres)

@app.route('/add_genre', methods=['GET', 'POST'])
@login_required
def add_genre():
    if request.method == 'POST':
        title = request.form['title']
        
        # Получаем максимальное значение ID из текущих записей
        max_genre_id = Genre.query.order_by(Genre.id.desc()).first().id
        
        # Задаем новый ID, увеличивая максимальное значение на 1
        new_genre_id = max_genre_id + 1 if max_genre_id else 1
        
        genre = Genre(id=new_genre_id, title=title)
        db.session.add(genre)
        db.session.commit()
        flash('Жанр успешно добавлен.', 'success')
        return redirect(url_for('admin_genres'))
    return render_template('admin_panel/add_genre.html')


@app.route('/edit_genre/<int:genre_id>', methods=['GET', 'POST'])
@login_required
def edit_genre(genre_id):
    genre = Genre.query.get_or_404(genre_id)
    if request.method == 'POST':
        genre.title = request.form['title']
        db.session.commit()
        flash('Жанр успешно обновлен.', 'success')
        return redirect(url_for('admin_genres'))
    return render_template('admin_panel/edit_genre.html', genre=genre)

@app.route('/delete_genre/<int:genre_id>', methods=['POST'])
@login_required
def delete_genre(genre_id):
    genre = Genre.query.get_or_404(genre_id)
    db.session.delete(genre)
    db.session.commit()
    flash('Жанр успешно удален.', 'success')
    return redirect(url_for('admin_genres'))


@app.route('/admin_groups', methods=['GET'])
@login_required
def admin_groups():
    groups = Group.query.all()
    return render_template('admin_panel/admin_groups.html', groups=groups)

@app.route('/add_group', methods=['GET', 'POST'])
@login_required
def add_group():
    if request.method == 'POST':
        title = request.form['title']
        id_book = request.form['book_id']
        
        new_group = Group(title=title, id_book=id_book)
        db.session.add(new_group)
        db.session.commit()
        return redirect(url_for('admin_groups'))

    books = Book.query.all()
    return render_template('admin_panel/add_group_form.html', books=books)

@app.route('/edit_group/<int:group_id>', methods=['GET', 'POST'])
@login_required
def edit_group(group_id):
    group = Group.query.get_or_404(group_id)
    if request.method == 'POST':
        group.title = request.form['title']
        group.id_book = request.form['book_id']
        db.session.commit()
        return redirect(url_for('admin_groups'))
    
    books = Book.query.all()
    return render_template('admin_panel/edit_group_form.html', group=group, books=books)

@app.route('/delete_group/<int:group_id>', methods=['POST'])
@login_required
def delete_group(group_id):
    group = Group.query.get_or_404(group_id)
    db.session.delete(group)
    db.session.commit()
    return redirect(url_for('admin_groups'))


@app.route('/rating_books', methods=['GET'])
@login_required
def rating_books():
    books_with_ratings = Rating.query.join(Book).order_by(Rating.rating.desc()).all()
    return render_template('admin_panel/admin_ratings.html', books_with_ratings=books_with_ratings)

@app.route('/add_rating', methods=['GET', 'POST'])
@login_required
def add_rating():
    if request.method == 'POST':
        rating_value = int(request.form['rating'])
        book_id = int(request.form['book_id'])
        
        existing_rating = Rating.query.filter_by(id_book=book_id).first()
        if existing_rating:
            existing_rating.rating = rating_value
        else:
            new_rating = Rating(rating=rating_value, id_book=book_id)
            db.session.add(new_rating)
        
        db.session.commit()
        return redirect(url_for('rating_books'))

    books = Book.query.all()
    return render_template('admin_panel/admin_add_rating.html', books=books)

@app.route('/delete_rating/<int:rating_id>', methods=['POST'])
@login_required
def delete_rating(rating_id):
    rating_to_delete = Rating.query.get_or_404(rating_id)
    db.session.delete(rating_to_delete)
    db.session.commit()
    return redirect(url_for('rating_books'))


@app.route('/admin_authors', methods=['GET', 'POST'])
@login_required
def admin_authors():
    if request.is_json:
        # Обработка AJAX-запроса
        if request.method == 'POST':
            new_name = request.json['name']
            new_author = Author(name=new_name)
            db.session.add(new_author)
            db.session.commit()
            return jsonify({'message': 'Автор успешно добавлен.'}), 201
    else:
        # Обработка обычных запросов
        if request.method == 'POST':
            new_name = request.form['name']
            new_author = Author(name=new_name)
            db.session.add(new_author)
            db.session.commit()
            flash('Автор успешно добавлен.', 'success')
            return redirect(url_for('admin_authors'))
        
        authors = Author.query.all()
        return render_template('admin_panel/admin_authors.html', authors=authors)

@app.route('/admin_authors/edit/<int:author_id>', methods=['POST'])
@login_required
def edit_author(author_id):
    # Редактирование автора
    author = Author.query.get(author_id)
    if not author:
        return jsonify({'error': 'Автор не найден'}), 404
    
    author.name = request.form['name']
    db.session.commit()
    flash('Информация об авторе успешно обновлена.', 'success')
    return redirect(url_for('admin_authors'))


@app.route('/admin_authors/delete/<int:author_id>', methods=['POST'])
@login_required
def delete_author(author_id):
    author = Author.query.get(author_id)
    if author:
        db.session.delete(author)
        db.session.commit()
        return jsonify({'message': 'Автор успешно удален.'}), 200
    else:
        return jsonify({'error': 'Автор не найден'}), 404


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        # Проверяем, существует ли пользователь с таким именем и электронной почтой
        user = Users.query.filter_by(email=email, password=password).first()
        if user:
            login_user(user)  # Если пользователь найден, авторизуем его

            return redirect(url_for('index'))  # Переход на страницу после успешного входа

        else:
            print("Пользователь не найден")
            flash('Неверное имя пользователя или электронная почта.', 'error')

    return render_template('login.html')


@app.route('/books')
def show_books():
    id_genre = request.args.get('id_genre', None)
    query = Book.query

    if id_genre:
        query = query.filter(Book.id_genre == id_genre)

    books = query.all()
    genres = Genre.query.all()

    # Вычисление среднего рейтинга для каждой книги
    ratings = Rating.query.with_entities(Rating.id_book, func.avg(Rating.rating).label('average_rating')).group_by(Rating.id_book).all()
    rating_dict = dict((r.id_book, r.average_rating) for r in ratings)

    return render_template('books.html', books=books, genres=genres, rating_dict=rating_dict)


@app.route('/terms')
def terms():
    return render_template('terms.html')


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    if query:
        book_query = f"%{query}%"
        author_query = f"%{query}%"
        
        logger.debug(f"Book query: {book_query}")
        logger.debug(f"Author query: {author_query}")
        
        # Поиск книг
        books = Book.query.filter(Book.title.contains(book_query)).all()
        
        # Поиск авторов
        authors = Author.query.filter(Author.name.contains(author_query)).all()
        
        logger.debug(f"Books found: {len(books)}")
        logger.debug(f"Authors found: {len(authors)}")
        
    else:
        books = []
        authors = []
    
    return render_template('search_results.html', books=books, authors=authors)


def get_book_by_id(book_id):
    book = db.session.query(Book).filter(Book.id == book_id).first()
    return book


@app.route('/detail/<int:book_id>')
def book_detail(book_id):
	# Получите информацию о книге из базы данных по ID
	book = get_book_by_id(book_id)
	# Вычисление среднего рейтинга для данной книги
	ratings = Rating.query.with_entities(func.avg(Rating.rating).label('average_rating')).filter(Rating.id_book == book_id).one_or_none()
	rating = ratings.average_rating if ratings else None
	return render_template('book_detail.html', book=book, rating=rating)

@app.template_filter('has_rating')
def has_rating(book_id, user_id=None):
    if user_id:
        rating = Rating.query.filter_by(id_book=book_id, id_user=user_id).first()
    else:
        rating = Rating.query.filter_by(id_book=book_id).first()
    return rating is not None


@app.route('/rate_book', methods=['POST'])
@login_required
def rate_book():
	# Проверяем, является ли текущий пользователь ghost
	if isinstance(current_user, AnonymousUserMixin):
		flash('Пожалуйста, войдите в систему, чтобы оставить оценку.', 'error')
		return redirect(url_for('login'))

	# Продолжаем выполнение, если пользователь вошел в систему
	id_book = request.form['id_book']
	rating_value = float(request.form['rating'])
	rounded_rating = round(rating_value, 2)

	# Получаем объект Role по идентификатору пользователяs
	role = Role.query.filter_by(id=current_user.id_role).first()

	# Проверяем, является ли пользователь одним из разрешенных
	if role and role.name!= 'user' and role.name!= 'admin':  # Изменено условие на проверку названия роли
		flash('У вас нет прав на оценку книг.', 'error')
		return redirect(url_for('index'))

	# Проверяем, уже ли пользователь оставил оценку для этой книги
	existing_rating = Rating.query.filter_by(id_user=current_user.id, id_book=id_book).first()
	if existing_rating:
		flash('Вы уже оставили оценку для этой книги.', 'error')
		return redirect(url_for('book_detail', book_id=id_book))

	# Создаем объект оценки и сохраняем его в базе данных
	rating = Rating(rating=rating_value, id_user=current_user.id, id_book=id_book)
	db.session.add(rating)
	db.session.commit()

	# После успешного сохранения оценки перенаправляем обратно на страницу детальной информации о книге
	return redirect(url_for('book_detail', book_id=id_book))


@app.route('/groups')
def show_groups():
    groups = Group.query.all()
    return render_template('groups.html', groups=groups)


@app.route('/add_comment', methods=['POST'])
@login_required
def add_comment():
    comment_text = request.form['comment_text']
    id_book = request.form['id_book']
    # Явно задаем дату комментария
    new_comment = Comment(text=comment_text, id_user=current_user.id, id_book=id_book, date=datetime.now(timezone.utc))
    db.session.add(new_comment)
    db.session.commit()
    flash('Комментарий успешно добавлен.', 'success')
    return redirect(url_for('book_detail', book_id=id_book))


@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    book_id = request.form['book_id']
    book = db.session.get(Book, book_id)
    if book:
        cart = Cart.query.filter_by(id_user=current_user.id).first()
        if not cart:
            cart = Cart(id_user=current_user.id)
            db.session.add(cart)
        
        # Проверяем, есть ли уже элемент корзины для этой книги
        existing_item = CartItem.query.filter_by(id_cart=cart.id, id_book=book_id).first()
        if existing_item:
            pass
        else:
            item = CartItem(id_cart=cart.id, id_book=book_id)
            db.session.add(item)
        
        db.session.commit()
        return redirect(url_for('show_books'))
    else:
        return jsonify({'error': 'Книга не найдена'}), 404


@app.route('/cart')
@login_required
def view_cart():
    cart = Cart.query.filter_by(id_user=current_user.id).first()
    if not cart:
        # Если корзина не найдена, создаем новую
        cart = Cart(id_user=current_user.id)
        db.session.add(cart)
        db.session.commit()

    items = CartItem.query.filter_by(id_cart=cart.id).all()
    # Фильтрация элементов корзины, чтобы исключить те, у которых нет книги
    valid_items = [item for item in items if item.book is not None]

    total_cost = sum([item.book.price * item.quantity for item in valid_items])

    return render_template('cart.html', items=valid_items, total_cost=total_cost)


@app.route('/remove_from_cart/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    # Получаем элемент корзины по ID
    cart_item = CartItem.query.get(item_id)

    if not cart_item:
        flash('Элемент корзины не найден.', 'error')
        return redirect(url_for('view_cart'))

    # Удаляем элемент из корзины
    db.session.delete(cart_item)
    db.session.commit()

    flash('Элемент корзины успешно удален.', 'success')
    return redirect(url_for('view_cart'))

	
@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    # Проверяем, существует ли корзина и содержит ли она элементы
    cart = Cart.query.filter_by(id_user=current_user.id).first()
    if not cart or not cart.items:
        flash('Ваша корзина пуста. Для оформления заказа добавьте товары в корзину.', 'error')
        return redirect(url_for('view_cart'))

    if request.method == 'POST':
        msg = Message("Subject of the Message",
                      sender="genger1356@mail.ru",
                      recipients=["ghostfless@mail.ru"],
                      body="Спасибо за ваш заказ Мы скоро свяжемся с вами.")

        msg.body = "Спасибо за ваш заказ. Вот детали:\n\n"
        items = CartItem.query.filter_by(id_cart=cart.id).all()
        valid_items = [item for item in items if item.book is not None]
        total_cost = sum([item.book.price * item.quantity for item in valid_items])

        # Отправьте сообщение
        for item in valid_items:
            msg.body += f"{item.book.title} - {item.book.price}₽ x {item.quantity}шт. = {item.book.price * item.quantity}₽\n"

        msg.body += f"\nОбщая сумма заказа: {total_cost}₽"

        # Отправка письма
        mail.send(msg)
        
        # Проверяем, существует ли корзина
        if cart:
            # Удаляем все элементы корзины
            delete_query = delete(CartItem).where(CartItem.id_cart == cart.id)
            db.session.execute(delete_query)
            
            # Обновляем корзину без элементов
            cart.items = []
            db.session.commit()

            # Передаем информацию в шаблон
            return render_template('order_confirmation.html', items=valid_items, total_cost=total_cost)

        else:
            flash('Корзина не найдена.', 'error')
            return redirect(url_for('index'))

    return render_template('checkout.html')


@app.route('/order_confirmation')
def order_confirmation():
    # Логика обработки подтверждения заказа
    return render_template('order_confirmation.html')


@app.route('/update_username', methods=['GET', 'POST'])
@login_required
def update_username():
    if request.method == 'POST':
        new_username = request.form.get('new_username')
        current_user.username = new_username
        db.session.commit()
        flash('Имя пользователя успешно обновлено.', 'success')
        return redirect(url_for('profile'))
    return render_template('profile_edit.html', user=current_user)



role_names = {
    1: 'Админ',
    2: 'Читатель',
    3: 'Гость'
}


def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploads', methods=['GET', 'POST'])
@login_required
def upload_excel():
    if current_user.id_role!= 1:  # Проверяем, является ли текущий пользователь администратором
        return abort(403)  # Запрещаем доступ для пользователей, не являющихся администраторами

    if request.method == 'POST':
        file = request.files['excel_file']
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Чтение данных из файла Excel
            df = pd.read_excel(filepath)
            
            # Преобразование DataFrame в HTML-таблицу
            html_table = df.to_html(index=False)
            
            # Отправка HTML-таблицы в шаблон
            return render_template('display.html', table=html_table)
    
    return render_template('upload.html')


@app.route('/upload_image', methods=['POST'])
@login_required
def upload_image():
    if 'photo' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['photo']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        image_url = url_for('static', filename=filename)
        return jsonify({'image_url': image_url})


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user, role_names=role_names)


@app.route('/logout')
@login_required
def logout():
    logout_user()  # Завершаем сеанс пользователя
    return redirect(url_for('index'))  # Переадресация на главную страницу после выхода


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/is_admin')
def is_admin():
    if current_user.is_authenticated and current_user.id_role == 1:
        return {"isAdmin": True}
    else:
        return {"isAdmin": False}

if __name__ == '__main__':
    app.run(debug=True, port=11111)