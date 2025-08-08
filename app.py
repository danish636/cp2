from flask import Flask

app = Flask(__name__)

# this is the entry point
application = app

@app.route("/")
def hello():
    return "Congratulation! You service Hosted on CPanel"

if __name__ == "__main__":
    app.run()