from flask import Flask, session, flash
from config import Config
from functools import wraps
import json, requests, getpass, logging, os
from logging.handlers import SMTPHandler, RotatingFileHandler
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from slackclient import SlackClient
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
Bootstrap(app)
mail = Mail(app)
slack_client = SlackClient(app.config['SLACK_TOKEN'])
scheduler = BackgroundScheduler()

from app import routes, models
from app import nsfunctions
from app import slackfunctions
from app import jobs

scheduler.add_job(
    func=jobs.kscnetattackscrape,
    trigger=IntervalTrigger(seconds=60),
    id='ksc_scraping_job',
    name='Scrape network attacks every hour',
    replace_existing=True)
scheduler.add_job(
    func=jobs.populate_ip_country,
    trigger=IntervalTrigger(seconds=90),
    id='ip_to_country_lookup_job',
    name='store origin country in DB',
    replace_existing=True)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())

if not app.debug:
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='alerts@realtracs.net',
            toaddrs=app.config['ADMINS'], subject='Devops Failure',
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/devops.log', maxBytes=10240,
                                       backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Devops startup')
