from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, desc
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

AUTH_KEY = 'auth_key'


class Base(DeclarativeBase):
    pass


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
Bootstrap5(app)

# CREATE DB
db = SQLAlchemy(model_class=Base)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movie.db"
# initialize the app with the extension
db.init_app(app)

# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(100), nullable=True)
    img_url: Mapped[str] = mapped_column(String(200), nullable=False)


class MyForm(FlaskForm):
    rating = StringField(u'Your Rating Out of 10 e.g. 7.5', name='rat', validators=[DataRequired()])
    review = StringField(u'Your Review', name='rev', validators=[DataRequired()])
    button = SubmitField('Done')


class AddForm(FlaskForm):
    title = StringField(u'Add Movie', name='title', validators=[DataRequired()])
    button = SubmitField('Add Movie')


with app.app_context():
    db.create_all()


@app.route("/")
def home():

    all_movies = Movie.query.order_by(desc(Movie.rating)).all()
    return render_template("index.html", movies=all_movies)


@app.route("/edit/<sid>", methods=['GET', 'POST'])
def edit(sid):
    if request.method == 'POST':
        movie_to_update = db.session.execute(db.select(Movie).where(Movie.id == sid)).scalar()
        movie_to_update.rating = float(request.form['rat'])
        movie_to_update.review = request.form['rev']
        db.session.commit()
        return redirect(url_for("home"))

    flask_form = MyForm()

    return render_template("edit.html", form=flask_form)


@app.route("/delete/<sid>", methods=['GET', 'POST'])
def delete(sid):

    with app.app_context():
        movie_to_delete = db.session.execute(db.select(Movie).where(Movie.id == sid)).scalar()
        db.session.delete(movie_to_delete)
        db.session.commit()

    return redirect(url_for("home"))


@app.route("/add", methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        movie_title = request.form['title']
        url = "https://api.themoviedb.org/3/search/movie"

        parameters = {
            "query": movie_title,
            "include_adult": "false",
            "language": "en - US",
            "page": 1,
        }

        headers = {
            "accept": "application/json",
            "Authorization": AUTH_KEY
        }
        response = requests.get(url, headers=headers, params=parameters).json()

        return render_template("select.html", movies=response['results'])

    add_form = AddForm()

    return render_template("add.html", form=add_form)


@app.route("/select/<mid>")
def select(mid):

    url = f"https://api.themoviedb.org/3/movie/{mid}?language=en-US"

    headers = {
        "accept": "application/json",
        "Authorization": AUTH_KEY
    }

    response = requests.get(url, headers=headers).json()
    yr = response['release_date'].split('-')
    img2 = f"https://image.tmdb.org/t/p/w500/{response['poster_path']}"
    new_movie = Movie(title=response['original_title'], year=int(yr[0]),
                      img_url=img2, description=response['overview'])
    db.session.add(new_movie)
    db.session.commit()
    movie_to_update = db.session.execute(db.select(Movie).where(Movie.title == response['original_title']
                                         and Movie.year == int(yr[0]))).scalar()
    return redirect(url_for("edit", sid=movie_to_update.id))


if __name__ == '__main__':
    app.run(debug=True)
