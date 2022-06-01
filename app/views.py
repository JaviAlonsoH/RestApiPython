from email import header
import json
import bson
from bson import ObjectId, json_util
from validator import validate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask import Response, jsonify, redirect, request, session
from app import app
from models.models import User
from flask_pymongo import PyMongo 

mongo_client = PyMongo(app)
jwt = JWTManager(app)

### LOGIN ###
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        rules = {
            "email": "required|mail",
            "password": "required|min:4"
        }
        if not data:
            return {
                "Message": 'Please provide user details.',
                "data": None,
                "error": "Bad request"
            }, 400
        ## Validating input
        validated = validate(data, rules)
        if validated is not True:
            return dict(message='Invalid request', data=None, error=validated), 400
        user_for_id = mongo_client.db.users.find_one({ "email": data['email'] })
        user = User().login(
            data['email'],
            data['password']
        )
        print('hola')
        if user:
            print('User exists')
            try:
                token = create_access_token(identity={ "email": user['email'], "user_id": json.loads(json_util.dumps(user_for_id['_id'])) })
                print('Token created, going straight to the authorization! ' + token)
                return {
                    "auth_token": token
                }
            except Exception as e:
                return {
                    "error": "Something went wrong",
                    "message": str(e)
                }, 500
        return {
            "message": "Error fetching auth token!, invalid email or password",
            "data": None,
            "error": "Unauthorized"
        }, 404
    except Exception as e:
        return {
                "message": "Something went wrong!",
                "error": str(e),
                "data": None
        }, 500

### HOME ENDPOINT ###
@app.route('/home', methods=['GET'])
def home():
        return 'CONGRATS!!!!!'


### USER ENDPOINTS ###
@app.route('/user/<id>', methods=['GET'])
def get_user(id):
    user_found = mongo_client.db.users.find_one({ '_id': ObjectId(id) })
    print(user_found)
    response = json_util.dumps(user_found)
    if user_found: 
        return Response(response, mimetype="application/json")
    else:
        return not_found()


@app.route('/newuser', methods=['POST'])
def create_user():
    ## Receiving data
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']

    if username and password and email:
        print('before response')
        response = User().create(username, password, email)
        print(response)
        return response 
    else:
        return not_found()

@app.route('/updateuser/<id>', methods=['UPDATE'])
def update_user(id):
    data = request.json
    user_updated = mongo_client.db.users.update_one({ '_id': ObjectId(id) }, { '$set': data })
    if user_updated:
        return { 'message': 'Your information has been updated!' }
    else:
        return not_found()

@app.route('/deleteuser/<id>', methods=['DELETE'])
def delete_user(id):
    user_deleted = mongo_client.db.users.delete_one({ '_id': ObjectId(id) })
    response = jsonify({ 'message': 'User ' + id + ' has been deleted.'})
    if user_deleted:
        return response
    else:
        return not_found()

@app.route('/<id>/settings/disableaccount')
def disable_account(self, id):
    user = mongo_client.db.users.update_one(
        {"_id": bson.ObjectId(id)},
        {"$set": {"active": False}}
    )
    user = self.get_by_id(id)
    return user

@app.route('/createhouse', methods=['POST'])

@app.errorhandler(404)
def not_found(error=None):
    response = jsonify({
        'error_message': 'Resource not found: ' + request.url,
        'status': 404
    })
    response.status_code = 404
    return response

def login(self, email, password):
    user = self.get_by_email(email)
    if not user or not check_password_hash(user["password"], password):
        return
    user.pop("password")
    return user
