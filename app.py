import datetime
import json
import sys
import os   

import requests
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

# create the extension object
db = SQLAlchemy()

# create the Flask app
app = Flask(__name__)

# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///weather.db"
app.secret_key = 'secret_key'

# initialize the app with the extension
db.init_app(app)

try:
    API_KEY = str(os.environ["API_KEY"])
except KeyError:
    sys.exit("Can't find api_key!")

URL = 'https://api.openweathermap.org/data/2.5/weather'


# create the database model
class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

    def __repr__(self):
        return f"City('{self.name}')"  # f-string


# create the database tables
with app.app_context():
    # db.drop_all()
    db.create_all()


# create the routes
@app.route('/')
def index():
    cities = City.query.all()
    weather_data = []
    for city in cities:
        weather = get_city_weather(city)
        weather_data.append(weather)
    return render_template('index.html', weather_data=weather_data)


@app.route('/delete/<city_id>', methods=['GET', 'POST'])
def delete(city_id):
    city = City.query.filter_by(id=city_id).first()
    db.session.delete(city)
    db.session.commit()
    return redirect('/')


@app.route('/add', methods=['POST'])
def add():
    if request.method == "POST":
        city = request.form.get('city_name')
        if len(city) > 60:
            flash('The name is too long!')
            return redirect('/')

        # city = request.form['city_name']
        exists = db.session.query(City.id).filter_by(name=city).first() is not None
        if exists:
            flash(f'The city has already been added to the list!')
            return redirect(url_for('index'))

        if not (is_city_real(city)) or city == "The city that doesn't exist!":
            flash("The city doesn't exist!")
            return redirect('/')

        if city:
            new_city = City(name=city)
            db.session.add(new_city)
            db.session.commit()
            return redirect(url_for('index'))


def is_city_real(city):
    city_params = {
        'q': city,
        'appid': API_KEY,
        'units': 'metric'
    }
    response = requests.get(URL, params=city_params)
    res = response.json()
    code_ = int(res["cod"])
    if 400 <= code_ < 500:
        return False
    return True


def get_city_weather(city):
    city_params = {
        'q': city.name,
        'appid': API_KEY,
        'units': 'metric'
    }
    city_weather = requests.get(URL, params=city_params)
    city_weather = json.loads(json.dumps(city_weather.json()))
    day_ = parse_unix_time(city_weather["dt"] + city_weather["timezone"])
    if 6 < day_ <= 18:
        day_ = 'day'
    elif 18 < day_ < 24:
        day_ = 'night'
    else:
        day_ = 'evening-morning'
    city_weather = {
        'city': city,
        'weather': city_weather['weather'][0]['main'],
        'temp': city_weather["main"]['temp'],
        'day_time': day_
    }
    return city_weather


def parse_unix_time(n):
    """
        A function that parses unix time stamp and returns the hour of the day as an integer
    """
    timestamp = datetime.datetime.fromtimestamp(n)
    timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    timestamp = timestamp.split(" ")
    time_ = int(timestamp[1].split(":")[0])
    return time_


# don't change the following way to run flask:

if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
