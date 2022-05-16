from datetime import timedelta
from flask import Flask

### API config
app = Flask(__name__)
app.config['MONGO_URI'] = "mongodb://localhost/tence"
app.config['SECRET_KEY'] = "213jsn3AJJ3iikn340"
app.config['TOKEN_EXPIRES_IN'] = timedelta(minutes=2)

from app import views
from auth import auth_middleware