import requests

BASE = "http://127.0.0.1:5000/"

response = requests.put(BASE + "message/1", {})
print(response.json())
input()
response = requests.put(BASE + "message/1", {})
print(response.json())