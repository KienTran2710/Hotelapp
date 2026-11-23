from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'hotel_pms_secret_key_ou_2026'
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:060906@localhost/hoteldb?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

db = SQLAlchemy(app=app)
