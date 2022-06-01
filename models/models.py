from array import array
from email.policy import default
import json
from tokenize import Number, String
import bson
from bson import ObjectId, json_util
from pymongo import MongoClient
from pymongo.errors import CollectionInvalid
from collections import OrderedDict
from flask_pymongo import PyMongo
from validator_collection import string
from werkzeug.security import generate_password_hash, check_password_hash
from app import app
from datetime import datetime 

mongo_client = PyMongo(app)

class Houses:
    def __init__(self):
        return

    def create(self, user_id:string, name:string, members:array, bills:object, shoplist:object, tasklist:array, homerules:object, house_img:string,):
        house = self.get_by_user_id(user_id)
        if house:
            return
        new_house = app.db.houses.insert_one(
            {
                "name": name,
                "members": [json.loads(json_util.dumps(ObjectId(user_id)))],
                "house_img": house_img,
                "bills": bills,
                "shoplist": shoplist,
                "tasklist": tasklist,
                "homerules": homerules,
                "created_at": datetime.now(),
                "created_by": user_id
            }
        )
        return self.get_by_id(new_house.inserted_id)

    def get_by_id(self, house_id):
        house = mongo_client.db.houses.find_one({"_id": bson.ObjectId(house_id)})
        if not house:
            return
        return json.dumps(house)

    def get_house_by_creator(self, user_id):
        house = mongo_client.db.houses.find({"created_by": user_id})
        if not house:
            return
        return json.dumps(house)

    def get_user_house(self, user_id):
        user = mongo_client.db.users.find({"_id": bson.ObjectId(user_id)})
        if not user:
            return
        user_house = mongo_client.db.houses.find_one({ "_id": bson.ObjectId(user['house'])})
        return json.dumps(user_house)

    def get_by_category(self, category):
        books = mongo_client.db.houses.find({"category": category})
        return [book for book in books]

    def delete(self, house_id):
        book = mongo_client.db.houses.delete_one({"_id": ObjectId(house_id)})
        return book

    def delete_by_user_id(self, user_id):
        house = mongo_client.db.houses.delete_many({"createdBy": ObjectId(user_id)})
        return house


### BILLS DOCUMENT
# "bills": {
#   "total_owe": 1500,
#   "distribution": [
#       {
#           "member_id": "ObjectId",
#           to_pay: 750
#       },
#       {
#           "member_id": "ObjectId",
#           to_pay: 750
#       }
#   ],
#   "list_of_bills": [
#   {
#       "name": "name of the bill",
#       "cost": 200
#   },
#   {
#       "name": "name of the bill",
#       "cost": 200
#   }
#   ]
# }
class Bills:
    def __init__(self):
        return

    def add_bill(self, user_id:string, total_owe:Number, distribution:array, list_of_bills:array):
        house = self.get_by_user_id(user_id)
        if house:
            return
        data = {
                "total_owe": total_owe,
                "distribution": distribution,
                "list_of_bills": list_of_bills
            }
        updated_bills = app.db.houses.update_one(
            { "created_by": user_id },
            { "$set": { "bills": data } }
        )
        return json.dumps(updated_bills)


### SHOPLIST DOCUMENT
# "shoplist": {
#   "total_owe": 1500,
#   "distribution": [
#       {
#           "member_id": "ObjectId",
#           "to_pay": 750
#       },
#       {
#           "member_id": "ObjectId",
#           "to_pay": 750
#       }
#   ],
#   "list_of_bills": [
#   {
#       "name": "name of the bill",
#       "cost": 200
#   },
#   {
#       "name": "name of the bill",
#       "cost": 200
#   }
#   ]
# }
class Shoplist:
    def __init__(self):
        return

    def update_common_shoplist(self, house_id:string, product_list:array):
        house = Houses.get_by_id(bson.ObjectId(house_id))
        if not house:
            return
        data = {
                "products": product_list,
            }
        updated_common_sl = app.db.houses.update_one(
            { "_id": bson.ObjectId(house_id) },
            { "$set": { "shoplist": data } }
        )
        return json.dumps(updated_common_sl)
    
    def update_personal_shoplist(self, user_id:string, total_owe:Number, distribution:array, list_of_bills:array):
        user = User.get_by_id(bson.ObjectId(user_id))
        if not user:
            return
        data = {
                {
                "total_owe": total_owe,
                "distribution": distribution,
                "list_of_bills": list_of_bills
                }
            }
        updated_document = app.db.users.update_one(
            { "_id": bson.ObjectId(user_id) },
            { "$set": { "personal_shoplist" : data } }
        )
        return json.dumps(updated_document)


### TASKLIST DOCUMENT
# "tasklist": [
#   {
#       task_name: "name",
#       "asigned_to": "ObjectId"
#   },
#   {
#       task_name: "name",
#       "asigned_to": "ObjectId"
#   },
#   {
#       task_name: "name",
#       "asigned_to": "ObjectId"
#   }
# ]

class Tasklist:
    def __init__(self):
        return

    def update_common_tasklist(self, house_id:string, task_name:string, task_description:string, asigned_to:string):
        house = Houses.get_by_id(bson.ObjectId(house_id))
        if not house:
            return
        data = {
                "task_name": task_name,
                "asigned_to": asigned_to
            }
        updated_common_tl= app.db.houses.update_one(
            { "_id": bson.ObjectId(house_id) },
            { "$set": { "tasklist": data } }
        )
        return json.dumps(updated_common_tl)
    
    def update_personal_tasklist(self, user_id:string, task_name:string, task_description:string):
        user = User.get_by_id(bson.ObjectId(user_id))
        if not user:
            return
        data = {
                "task_name": task_name,
                "task_description": task_description
            }
        updated_common_tl= app.db.users.update_one(
            { "_id": bson.ObjectId(user_id) },
            { "$set": { "tasklist": data } }
        )
        return json.dumps(updated_common_tl)


class User:
    def __init__(self):
        return

    def create(self, username="", password="", email=""):
        user = self.get_by_email(email)
        if user:
            return
        new_user = mongo_client.db.users.insert_one(
            {
                "username": username,
                "email": email,
                "password": self.encrypt_password(password),
                "house": "",
                "active": True,
                "have_to_pay": 0.0,
                "personal_shoplist": [],
                "personal_tasklist": [],
                "tasks_assigned": [],
                "rules_accepted": False
            }
        )
        print('hola')
        return json.dumps(self.get_by_id(new_user.inserted_id))

    def get_all(self):
        users = mongo_client.db.users.find({"active": True})
        return [{**user, "_id": str(user["_id"])} for user in users]

    def get_by_id(self, user_id):
        user = mongo_client.db.users.find_one({"_id": ObjectId(user_id), "active": True} )
        if not user:
            return
        return user

    def get_by_email(self, email):
        user = mongo_client.db.users.find_one({"email": email, "active": True})
        if not user:
            return
        return json.loads(json_util.dumps(user))

    def update_email(self, user_id, email:string):
        data = {}
        if email:
            if mongo_client.db.users.find({ "email": email }):
                return
        data["email"] = email
        user = mongo_client.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": data
            }
        )
        user = self.get_by_id(user_id)
        return user

    def delete(self, user_id):
        Houses().delete_by_user_id(user_id)
        user = mongo_client.db.users.delete_one({"_id": ObjectId(user_id)})
        user = self.get_by_id(user_id)
        return json.dumps(user)

    def disable_account(self, user_id):
        user = mongo_client.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"active": False}}
        )
        user = self.get_by_id(user_id)
        return json.dumps(user)

    def encrypt_password(self, password):
        return generate_password_hash(password)

    def login(self, email, password):
        user = self.get_by_email(email)
        if not user or not check_password_hash(user["password"], password):
            return
        user.pop("password")
        return json.loads(json_util.dumps(user))
