from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Pranika Baal Sewa website is working!"