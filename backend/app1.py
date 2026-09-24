from flask import Flask
from flask_cors import CORS
from blueprints import register_blueprints

app = Flask(__name__)
CORS(app)
register_blueprints(app)

if __name__ == '__main__':
    app.run(debug=True, port=11451, use_reloader=False)
