import bson
from bson import ObjectId, json_util
from pymongo import MongoClient
from pymongo.errors import CollectionInvalid
from collections import OrderedDict
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from app import app

mongo_client = PyMongo(app)

class Houses:
    def __init__(self):
        return

    def create(self, name="", members=[], bills={}, shoplist={}, tasklist={}, homerules={}, house_img="", createdAt="", createdBy=""):
        house = self.get_by_user_id(createdBy)
        if house:
            return
        new_house = app.db.houses.insert_one(
            {
                "name": name,
                "members": members,
                "bills": bills,
                "shoplist": shoplist,
                "tasklist": tasklist,
                "homerules": homerules,
                "house_img": house_img,
                "createdAt": createdAt,
                "createdBy": createdBy
            }
        )
        return self.get_by_id(new_house.inserted_id)

    def get_by_id(self, house_id):
        house = mongo_client.db.houses.find_one({"_id": ObjectId(house_id)})
        if not house:
            return
        house["_id"] = str(house["_id"])
        return house

    def get_by_user_id(self, user_id):
        houses = mongo_client.db.houses.find({"user_id": user_id})
        return [{**houses, "_id": str(house["_id"])} for user in users]

    def get_by_category(self, category):
        books = mongo_client.db.houses.find({"category": category})
        return [book for book in books]

    def delete(self, house_id):
        book = mongo_client.db.houses.delete_one({"_id": ObjectId(house_id)})
        return book

    def delete_by_user_id(self, user_id):
        house = mongo_client.db.houses.delete_many({"createdBy": ObjectId(user_id)})
        return house


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
                "active": True
            }
        )
        print('hola')
        return json_util.dumps(self.get_by_id(new_user.inserted_id))

    def get_all(self):
        users = mongo_client.db.users.find({"active": True})
        return [{**user, "_id": str(user["_id"])} for user in users]

    def get_by_id(self, user_id):
        user = mongo_client.db.users.find_one({"_id": ObjectId(user_id), "active": True})
        if not user:
            return
        return user

    def get_by_email(self, email):
        user = mongo_client.db.users.find_one({"email": email, "active": True})
        if not user:
            return
        user["_id"] = str(user["_id"])
        return user

    def update(self, user_id, name=""):
        data = {}
        if name:
            data["name"] = name
        user = mongo_client.db.users.update_one(
            {"_id": bson.ObjectId(user_id)},
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
        return user

    def disable_account(self, user_id):
        user = mongo_client.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"active": False}}
        )
        user = self.get_by_id(user_id)
        return user

    def encrypt_password(self, password):
        return generate_password_hash(password)

    def login(self, email, password):
        user = self.get_by_email(email)
        if not user or not check_password_hash(user["password"], password):
            return
        user.pop("password")
        return user
