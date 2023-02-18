from flask import Flask, request, render_template, redirect, url_for
import requests
import sys
import json
import datetime
from flask_sqlalchemy import SQLAlchemy

# create the extension object
db = SQLAlchemy()

# create the Flask app
app = Flask(__name__)

# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///weather.db"

# initialize the app with the extension
db.init_app(app)

API_KEY = '9c9072711700a5cf8bc1cd518bcb1db4'
URL = 'https://api.openweathermap.org/data/2.5/weather'

# create the database model
class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

    def __repr__(self):
        return f"City('{self.name}')"  # f-string

# create the database tables
with app.app_context():
    db.create_all()


# create the routes
@app.route('/')
def index():
    cities = City.query.all()
    weather_data = []
    for city in cities:
        weather = get_city_weather(city.name)
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
        if city:
            new_city = City(name=city)
            db.session.add(new_city)
            db.session.commit()
            return redirect(url_for('index'))
        redirect(url_for('index'))
        

def get_city_weather(city):
    params = {'q': city,
              'limit': 1,
              'appid': API_KEY}
    # city_res = requests.get(f'http://api.openweathermap.org/data/2.5/forecast?id=524901&appid={API_KEY}')
    city_res = requests.get('http://api.openweathermap.org/geo/1.0/direct', params=params).json()
    city_res = json.dumps(city_res)
    new_city_res = json.loads(city_res)
    city_params = {
        'lat': new_city_res[0]["lat"],
        'lon': new_city_res[0]["lon"],
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
        'city': city_weather['name'],
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
