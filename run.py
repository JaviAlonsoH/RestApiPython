from email import message
from functools import wraps
from msilib import init_database
import bson
from werkzeug import Response
from flask import request, jsonify, session, Blueprint
from datetime import datetime, timedelta
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson import json_util
from bson.objectid import ObjectId
import jwt
from validator import validate
from app import app

if __name__ == "__main__":
    app.run(debug=True)
