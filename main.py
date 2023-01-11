from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests


MOVIE_DB_API_KEY = "1939b79cec29c1183eddd06eed5a305e"
read_access_token = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIxOTM5Yjc5Y2VjMjljMTE4M2VkZGQwNmVlZDVhMzA1ZSIsInN1YiI6IjYzYmVjNzgyNWJlMDBlMDA4NDYzZDk5ZiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.Ogdte9bVT8ZKmjqYvOa3SejSXIC1AjRLEGNBT_bLhV4"
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Bootstrap(app)

db = SQLAlchemy(app, session_options={'expire_on_commit': False})

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

with app.app_context():
    db.create_all()


class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")


class AddMovieForm(FlaskForm):
    movie_title = StringField("Movie Title")
    submit = SubmitField("Add Movie")
# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
#
# with app.app_context():
#     db.session.add(new_movie)
#     db.session.commit()

@app.route("/")
def home():
    with app.app_context():
        all_movies = db.session.query(Movie).order_by(Movie.rating).all()
        print(all_movies)
        for i in range(len(all_movies)):
            # This line gives each movie a new ranking reversed from their order in all_movies
            all_movies[i].ranking = len(all_movies) - i
        db.session.commit()

    return render_template("index.html", movies=all_movies)


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddMovieForm()
    if form.validate_on_submit():
        movie_title = form.movie_title.data
        response = requests.get(MOVIE_DB_SEARCH_URL, params={"api_key": MOVIE_DB_API_KEY, "query": movie_title}).json()
        return render_template("select.html", data=response['results'])
    return render_template("add.html", form=form)


@app.route("/update", methods=["GET", "POST"])
def update():
    with app.app_context():
        form = RateMovieForm()
        movie_id = request.args.get("id")
        selected_movie = Movie.query.get(movie_id)
        if form.validate_on_submit():
            selected_movie.rating = float(form.rating.data)
            selected_movie.review = form.review.data
            db.session.commit()
            return redirect(url_for("home"))
    return render_template("edit.html", movie=selected_movie, form=form)


@app.route("/delete")
def delete():
    with app.app_context():
        movie_id = request.args.get("id")
        movie_to_delete = Movie.query.get(movie_id)
        db.session.delete(movie_to_delete)
        db.session.commit()
    return redirect(url_for("home"))


@app.route("/select")
def select():
    movie_id = int(request.args.get("id"))
    movie_api_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    response = requests.get(movie_api_url, params={"api_key": MOVIE_DB_API_KEY, "language": "en-US"}).json()

    new_movie = Movie(
        title=response["title"],
        year=response["release_date"].split("-")[0],
        description=response["overview"],
        img_url=f"https://www.themoviedb.org/t/p/original{response['poster_path']}",
    )

    with app.app_context():
        db.session.add(new_movie)
        db.session.commit()
        db_movie_id = Movie.query.filter_by(title=f"{response['title']}").first().id
        print(db_movie_id)
    return redirect(url_for("update", id=db_movie_id))


if __name__ == '__main__':
    app.run(debug=True)
