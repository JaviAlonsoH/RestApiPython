from email import header
from functools import wraps
import json
import bson
from bson import ObjectId, json_util
from jwt import DecodeError, decode
import jwt
from validator import validate
from flask import request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt, verify_jwt_in_request, get_jwt_identity, set_access_cookies
from flask_jwt_extended.exceptions import WrongTokenError
from flask import Response, current_app, jsonify, redirect, request, session
from validator_collection import datetime
from app import app
from models.models import Bills, Shoplist, Tasklist, User, Houses
from flask_pymongo import PyMongo 
from datetime import datetime, timedelta, timezone
import re

mongo_client = PyMongo(app)
jwt_manager = JWTManager(app)

def jwt_required_custom(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = request.headers['Authorization'].split(' ').pop()
        if not token:
            return 'Unauthorized', 401
        return fn(*args, **kwargs)
    return wrapper

@app.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        return response

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
        print('login validated')
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
@app.route('/home', methods=['POST'])
def home():
    house = Houses.get_user_house(request.json['email'])
    print(json_util.dumps(house))
    return house


### USER ENDPOINTS ###
@app.route('/getuser', methods=['POST'])
def get_user():
    user = User.get_by_email(request.json['email']) 
    print(user)
    return user


@app.route('/userhashouse', methods=['POST'])
def user_has_house():
    user_found = mongo_client.db.users.find_one({ 'email': request.json['email'] })
    print(user_found)
    if json.loads(json_util.dumps(user_found['house'])) == "":
        return json.dumps({"res": False})
    else:
        return json.dumps({"res": True})


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

## HOUSE ENDPOINTS ##
@app.route('/createhouse', methods=['POST'])
@jwt_required()
def create_house():
    data = request.json
    data = json.loads(json_util.dumps(data))
    members = data['members']
    print(data)
    Houses.create(
        email=data['email'], 
        name=data['name'],
        members=data['members'],
        bills=data['bills'],
        shoplist=data['shoplist'],
        tasklist=data['tasklist'],
        homerules=data['homerules'],
        house_img=data['house_img'],
        created_at=datetime.now(),
    )
    return json.dumps({"msg": "Casa creada con éxito."})

## BILLS ENDPOINTS ## 
@app.route('/getbills', methods=['POST'])
def get_bills():
    try:
        bills = Bills.get_bills(request.json['email'])
        return bills
    except:
        return json.dumps({ "error": "Ops, something failed..."})

@app.route('/getamounttopay', methods=['POST'])
def get_amount_to_pay():
    try:
        amount = Bills.get_amount_to_pay(request.json['email'])
        return amount
    except:
        return json.dumps({ "error": "Ops, something failed..."})

@app.route('/newbill', methods=['POST'])
@jwt_required()
def add_bill():
    try:
        Bills.add_bill(request.json['email'], request.json['bill_name'], request.json['bill_amount'], request.json['personal_cost'])
        return json.dumps({ "msg": "Bill added succesfully!"})
    except:
        return json.dumps({ "error": "Ops, something failed..."})

@app.route('/deletebill', methods=['POST'])
@jwt_required_custom
def delete_bill():
    try:
        Bills.delete_bill(request.json['email'], request.json['bill_name'], request.json['bill_cost'], request.json['personal_cost'])
        return json.dumps({ "msg": "Bill deleted succesfully!"})
    except:
        return json.dumps({ "error": "Ops, something failed..."})


## SHOPLIST ENDPOINTS ## 
@app.route('/getcommonlist', methods=['POST'])
def get_common_shopping_list(): 
    shoplist = Shoplist.get_common_shopping_list(request.json['email'])
    return shoplist

@app.route('/getpersonallist', methods=['POST'])
def get_personal_shopping_list(): 
    shoplist = Shoplist.get_personal_shopping_list(request.json['email'])
    return shoplist

@app.route('/deletecommonproduct', methods=['POST'])
def delete_common_product(): 
    try:
        Shoplist.delete_common_product(request.json['email'], request.json['product_name'])
        return json.dumps({ "msg": "Product deleted succesfully!"})
    except:
        return json.dumps({ "error": "Ops, something failed..."})

@app.route('/deletepersonalproduct', methods=['POST'])
def delete_personal_product(): 
    try:
        Shoplist.delete_personal_product(request.json['email'], request.json['product_name'])
        return json.dumps({ "msg": "Product deleted succesfully!"})
    except:
        return json.dumps({ "error": "Ops, something failed..."})

@app.route('/addcommonproduct', methods=['POST'])
def add_common_product():
    try:
        Shoplist.add_common_product(request.json['email'], request.json['product_name'], request.json['quantity'])
        return json.dumps({ "msg": "Product added succesfully!"})
    except:
        return json.dumps({ "error": "Ops, something failed..."})

@app.route('/addpersonalproduct', methods=['POST'])
def add_personal_product():
    try:
        Shoplist.add_personal_product(request.json['email'], request.json['product_name'], request.json['quantity'])
        return json.dumps({ "msg": "Product added succesfully!"})
    except:
        return json.dumps({ "error": "Ops, something failed..."})


# TASKLIST ENDPOINTS ## 
@app.route('/getcommontasklist', methods=['POST'])
def get_common_task_list(): 
    shoplist = Tasklist.get_common_task_list(request.json['email'])
    return shoplist

@app.route('/getpersonaltasklist', methods=['POST'])
def get_personal_task_list(): 
    shoplist = Tasklist.get_personal_task_list(request.json['email'])
    return shoplist

@app.route('/deletecommontask', methods=['POST'])
def delete_common_task():
    try:
        Tasklist.delete_common_task(request.json['email'], request.json['task_name'])
        return json.dumps({ "msg": "Product deleted succesfully!"})
    except:
        return json.dumps({ "error": "Ops, something failed..."})

@app.route('/deletepersonaltask', methods=['POST'])
def delete_personal_task():
    try:
        Tasklist.delete_personal_task(request.json['email'], request.json['task_name'])
        return json.dumps({ "msg": "Product deleted succesfully!"})
    except:
        return json.dumps({ "error": "Ops, something failed..."})

@app.route('/addcommontask', methods=['POST'])
def add_common_task(): 
    try:
        Tasklist.add_common_task(request.json['email'], request.json['task_name'])
        return json.dumps({ "msg": "Task added succesfully!"})
    except:
        return json.dumps({ "error": "Ops, something failed..."})

@app.route('/addpersonaltask', methods=['POST'])
def add_personal_task():
    try:
        Tasklist.add_personal_task(request.json['email'], request.json['task_name'])
        return json.dumps({ "msg": "Task added succesfully!"})
    except:
        return json.dumps({ "error": "Ops, something failed..."})

@app.errorhandler(404)
def not_found(error=None):
    response = jsonify({
        'error_message': 'Resource not found: ' + request.url,
        'status': 404
    })
    response.status_code = 404
    return response 
