from datetime import timedelta
from flask import Flask
from flask_cors import CORS

### API config
app = Flask(__name__)
CORS(app)
app.config['MONGO_URI'] = "mongodb://localhost/tence"
app.config['SECRET_KEY'] = "213jsn3AJJ3iikn340"
app.config['TOKEN_EXPIRES_IN'] = timedelta(minutes=10)

from app import views