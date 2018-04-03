import subprocess
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from flask import Flask, render_template, request, redirect, url_for
from wtforms import Form, SelectMultipleField, SelectField
import sqlite3
from datetime import date
import os
from find_connection import find_connection

COUNTRIES = [("au", "Australia"), ("ar", "Argentina"),("am", "Armenia"),
             ("by", "Belarus"),
             ("bg", "Bulgary"), ("br", "Brazil"), ("gb", "Great Britain"),
             ("de", "Germany"),
             ("gr", "Greece"), ("ge", "Georgia"), ("in", "India"),
             ("it", "Italy"),
             ("kz", "Kazakhstan"), ("ca", "Canada"), ("mx", "Mexica"),
             ("nl", "Netherlands"),
             ("ae", "UAE"), ("pt", "Portugal"), ("ru", "Russia"),
             ("ro", "Romania"), ("us", "USA"),
             ("sg", "Singapore"), ("tr", "Turkey"), ("uz", "Uzbekistan"),
             ("ua", "Ukraine"),
             ("fi", "Finland"), ("fr", "France"), ("cz", "Czech Republic"),
             ("ch", "Switzerland"),
             ("ee", "Estonia"), ("jp", "Japan")]

PERIODS = [("online","online"), ("hour","hour"),( "day",  "day"), ("week","week"), ("month","month")]

process = CrawlerProcess(get_project_settings())

def run(**kwargs):
    c = kwargs.get('countries')
    if type(c) == 'list':
        c = ', '.join(c)
    period = kwargs.get('period')
    process.crawl('news', countries=c, period=period)
    process.start() # the script will block here until the crawling is finished


app = Flask(__name__)


class BaseForm(Form):
    period = SelectField("Period", choices=PERIODS)
    countries = SelectMultipleField("Countries", choices=COUNTRIES)

DB_PATH = os.path.join(os.path.dirname(__file__), 'db','topnews.db')

@app.route("/", methods=["GET"])
def index():
    period = request.args.get("period")
    countries = request.args.getlist("countries")
    if period and countries:
        return show_network(period, countries)
    else:
        form = BaseForm(request.form)
        return render_template("base.html", form=form)

def show_network(period, countries):
    run(countries=countries, period=period)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    today = str(date.today())
    c.execute("SELECT * FROM topnews WHERE scraping_date=? and scraping_type=?",(today,period))
    news = c.fetchall()
    news_list = []

    for item in news:
        d = {'url': item[1], 'title': item[2], 'number': item[3], 'country': item[4]}
        news_list.append(d)

    edges = find_connection(news)
    print(news_list)
    return render_template("graph.html", listt=news_list, conns=edges)

if __name__ == "__main__":
    app.run(threaded=True)
