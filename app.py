from flask import Flask, request, render_template
import requests
import sys
import json
import datetime

app = Flask(__name__)

API_KEY = ''
URL = 'https://api.openweathermap.org/data/2.5/weather'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/add', methods=['POST'])
def add():
    if request.method == "POST":
        city = request.form.get('city_name')
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
        return render_template('index.html', city_weather=city_weather)



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
