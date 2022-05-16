from functools import wraps
import flask
from flask_jwt_extended import jwt_required, get_jwt_identity,JWTManager
from flask import redirect, request, abort, current_app, session
from models.models import User
from app import app

jwt = JWTManager(app)

@app.route('/auth', methods=['POST'])
@jwt_required()
def auth():
    user = get_jwt_identity()
    print(user)
    print('Authorizating!')
    return 'Access granted. Welcome!', 200
    
    
