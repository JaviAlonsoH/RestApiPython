from array import array
from email.policy import default
import json
from tokenize import Number, String
from unicodedata import numeric
import bson
from bson import ObjectId, json_util
from flask import jsonify
from matplotlib.font_manager import FontProperties
from pymongo import MongoClient
from pymongo.errors import CollectionInvalid
from collections import OrderedDict
from flask_pymongo import PyMongo
from validator_collection import string
from werkzeug.security import generate_password_hash, check_password_hash
from app import app
from datetime import datetime 

mongo_client = PyMongo(app)
houses = mongo_client.db['houses']
users = mongo_client.db['users']

class Houses:
    def __init__(self):
        return

    def create(email:string, name:string, members:array, bills:object, shoplist:object, tasklist:array, homerules:object, house_img:string, created_at: string):
        house = Houses.get_user_house(email)
        new_house = mongo_client.db.houses.insert_one(
            {
                "name": name,
                "members": members,
                "house_img": house_img,
                "bills": bills,
                "shoplist": shoplist,
                "tasklist": tasklist,
                "homerules": homerules,
                "created_at": created_at,
                "created_by": email
            }
        )
        mongo_client.db.users.update_one({"email": email}, {"$set": { "house": new_house.inserted_id}})
        return Houses.get_by_id(new_house.inserted_id)

    def get_by_id(house_id):
        house = mongo_client.db.houses.find_one({"_id": bson.ObjectId(house_id)})
        if not house:
            return
        return json.loads(json_util.dumps(house))

    def get_house_by_creator(email):
        house = mongo_client.db.houses.find({"created_by": email})
        if not house:
            return
        return json.loads(json_util.dumps(house))

    def get_user_house(email):
        try:
            user = User.get_by_email(email)
            if not user:
                return json.dumps({"msg": "The user provided was not found."})
            house = houses.find_one({ "_id": {user['house']} })
            print('HOUSE FOUND: ' + house)
            return json.loads(json_util.dumps(house))
        except:
            return json.dumps({"msg": "An error ocurred while getting the house info."})

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
#   "list_of_bills": [
#   {
#       "name": "name of the bill",
#       "cost": 200,
#       "personal_cost": 100
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

    def get_bills(email:string):
        try:
            user = User.get_by_email(email)
            oid = user['house']['$oid']
            house = Houses.get_by_id(oid)
            bills = house['bills']
            return json.dumps(bills)
        except:
            return json.dumps({ "error": "An error ocurred while loading the bills info" })

    def get_amount_to_pay(email:string):
        try:
            user = User.get_by_email(email) 
            bills = float(user['have_to_pay'])
            print(bills)
            return json.dumps(bills)
        except:
            return json.dumps({ "error": "An error ocurred while loading the info" })

    def add_bill(email:string, billName:string, amount:numeric, personal_cost:numeric):
        user = User.get_by_email(email)
        oid = user['house']['$oid']
        house = Houses.get_by_id(oid)
        if not house:
            return
        data = {
                "name": billName,
                "cost": amount,
                "personal_cost": personal_cost
            }
        updated_bills = mongo_client.db.houses.update_one(
            { "_id": ObjectId(str(house['_id']['$oid'])) },
            { "$push": {"bills.list_of_bills": data } }, True
        )
        if updated_bills:
            total_owe = house['bills']['total_owe']
            new_total_owe = total_owe + float(amount)
            mongo_client.db.houses.update_one(
                { "_id": ObjectId(str(house['_id']['$oid'])) },
                { "$set": {"bills.total_owe": new_total_owe  } }
            )
            user_owe = user['have_to_pay']
            new_user_owe = float(user_owe) + personal_cost
            mongo_client.db.users.update_one(
                { "_id": ObjectId(str(oid)) },
                { "$set": {"have_to_pay": new_user_owe  } }
            )
        return json.dumps(updated_bills)

    def delete_bill(email:string, name:string, bill_cost:numeric, personal_cost:numeric):
        user = User.get_by_email(email)
        oid = user['house']['$oid']
        house = Houses.get_by_id(oid)
        print('before the if')
        if not house:
            return
        bill_to_delete = mongo_client.db.houses.find_one(
            {"bills.list_of_bills.name": name},
            {"list_of_bills": {"$elemMatch": {"name": name}}}
        )
        if bill_to_delete:
            total_owe = house['bills']['total_owe']
            print(total_owe)
            print(bill_cost)
            new_value = float(total_owe) - float(bill_cost)
            print(new_value)
            print(user['_id']['$oid'])
            mongo_client.db.houses.update_one(
                { "_id": ObjectId(str(oid)) },
                { "$set": {"bills.total_owe": new_value } }
            )
            print('total changed')
            user_owe = user['have_to_pay']
            print(user_owe)
            new_user_owe = int(user_owe) - int(personal_cost)
            print(new_user_owe)
            mongo_client.db.users.update_one(
                { "_id": ObjectId(str(user['_id']['$oid'])) },
                { "$set": { "have_to_pay": new_user_owe } }
            )
            print('personal changed')
            mongo_client.db.houses.update_one(
            { "_id": ObjectId(str(oid)) },
            { "$pull": {"bills.list_of_bills": {"name": name} } }
            )
            print('pulled out')


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

    def get_common_shopping_list(email:string):
        try:
            user = User.get_by_email(email)
            oid = user['house']['$oid']
            house = Houses.get_by_id(oid)
            shoplist = house['shoplist']
            return json.dumps(shoplist)
        except:
            return json.dumps({ "error": "An error ocurred while loading the bills info" })
    
    def delete_common_product(email:string, product_name:string):
        try:
            user = User.get_by_email(email)
            oid = user['house']['$oid']
            house = Houses.get_by_id(oid)
            if not house:
                return
            product_to_delete = mongo_client.db.houses.find_one(
            {"shoplist.common_shoplist.product_name": product_name},
            {"list_of_bills": {"$elemMatch": {"product_name": product_name}}}
            )
            if product_to_delete:
                mongo_client.db.houses.update_one(
                { "_id": ObjectId(str(oid)) },
                { "$pull": {"shoplist.common_shoplist": {"product_name": product_name} } }
                )
                print('product pulled out')
        except:
            return json.dumps({ "error": "An error ocurred while loading the bills info" })

    def add_common_product(email:string, product_name:string, quantity:numeric):
        user = User.get_by_email(email)
        oid = user['house']['$oid']
        house = Houses.get_by_id(oid)
        if not house:
            return
        data = {
                "product_name": product_name,
                "quantity": quantity
            }
        mongo_client.db.houses.update_one(
            { "_id": ObjectId(str(oid)) },
            { "$push": {"shoplist.common_shoplist": data } }, True
        )
    
    def get_personal_shopping_list(email:string):
        try:
            user = User.get_by_email(email)
            shoplist = user['personal_shoplist']
            return json.dumps(shoplist)
        except:
            return json.dumps({ "error": "An error ocurred while loading the bills info" })
    
    def delete_personal_product(email:string, product_name:string):
        user = User.get_by_email(email)
        if not user:
            return
        product_to_delete = mongo_client.db.users.find_one(
        {"personal_shoplist.product_name": product_name},
        {"personal_shoplist": {"$elemMatch": {"product_name": product_name}}}
        )
        if product_to_delete:
            mongo_client.db.users.update_one(
            { "_id": ObjectId(str(user['_id']['$oid'])) },
            { "$pull": {"personal_shoplist": {"product_name": product_name} } }
            )
            print('product pulled out')

    def add_personal_product(email:string, product_name:string, quantity:numeric):
        user = User.get_by_email(email)
        if not user:
            return
        data = {
                "product_name": product_name,
                "quantity": quantity
            }
        mongo_client.db.users.update_one(
            { "_id": ObjectId(str(user['_id']['$oid'])) },
            { "$push": {"personal_shoplist": data } }, True
        )

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

    def get_common_task_list(email:string):
        try:
            user = User.get_by_email(email)
            oid = user['house']['$oid']
            house = Houses.get_by_id(oid)
            tasklist = house['tasklist']
            return json.dumps(tasklist)
        except:
            return json.dumps({ "error": "An error ocurred while loading the tasks info" })
    
    def delete_common_task(email:string, task_name:string):
        try:
            user = User.get_by_email(email)
            oid = user['house']['$oid']
            house = Houses.get_by_id(oid)
            if not house:
                return
            task_to_delete = mongo_client.db.houses.find_one(
            {"tasklist.task_name": task_name},
            {"tasklist": {"$elemMatch": {"task_name": task_name}}}
            )
            if task_to_delete:
                mongo_client.db.houses.update_one(
                { "_id": ObjectId(str(oid)) },
                { "$pull": {"tasklist": {"task_name": task_name} } }
                )
                print('task pulled out')
        except:
            return json.dumps({ "error": "An error ocurred while loading the bills info" })

    def add_common_task(email:string, task_name:string):
        user = User.get_by_email(email)
        oid = user['house']['$oid']
        house = Houses.get_by_id(oid)
        if not house:
            return
        data = {
                "task_name": task_name
            }
        mongo_client.db.houses.update_one(
            { "_id": ObjectId(str(oid)) },
            { "$push": {"personal_tasklist": data } }, True
        )

    def get_personal_task_list(email:string):
        try:
            user = User.get_by_email(email)
            tasklist = user['personal_tasklist']
            return json.dumps(tasklist)
        except:
            return json.dumps({ "error": "An error ocurred while loading the bills info" })
    
    def delete_personal_task(email:string, task_name:string):
        user = User.get_by_email(email)
        if not user:
            return
        task_to_delete = mongo_client.db.users.find_one(
        {"personal_tasklist.task_name": task_name},
        {"personal_tasklist": {"$elemMatch": {"task_name": task_name}}}
        )
        if task_to_delete:
            mongo_client.db.users.update_one(
            { "_id": ObjectId(str(user['_id']['$oid'])) },
            { "$pull": {"personal_tasklist": {"task_name": task_name} } }
            )
            print('task pulled out')

    def add_personal_task(email:string, product_name:string):
        user = User.get_by_email(email)
        if not user:
            return
        data = {
                "task_name": product_name
            }
        mongo_client.db.users.update_one(
            { "_id": ObjectId(str(user['_id']['$oid'])) },
            { "$push": {"personal_tasklist": data } }, True
        )
    

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
            { "$set": { "personal_tasklist": data } }
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

    def create(self, username:string, password:string, email:string):
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
        return json.dumps(self.get_by_id(new_user.inserted_id))

    def get_all(self):
        users = mongo_client.db.users.find({"active": True})
        return [{**user, "_id": str(user["_id"])} for user in users]

    def get_by_id(self, user_id):
        user = mongo_client.db.users.find_one({"_id": ObjectId(user_id), "active": True} )
        if not user:
            return
        return user

    def get_by_email(email):
        try:
            user = users.find_one({"email": email, "active": True})
            if not user:
                return json.dumps({ "error": "User not found."})
            return json.loads(json_util.dumps(user))
        except:
            return json.dumps({ "error": "Unexpected error"})

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
        user = User.get_by_email(email)
        if not user or not check_password_hash(user["password"], password):
            return
        user.pop("password")
        return json.loads(json_util.dumps(user))
