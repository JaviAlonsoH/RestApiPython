from flask import Flask
from flask_restful import Api, Resource, reqparse

app = Flask(__name__)
api = Api(app)

msg_put_args = reqparse.RequestParser()
msg_put_args.add_argument("msg_body", type=str, help="Type something", required=True)

messages = {}


class Message(Resource):
    def get(self, msg_id):
        return messages[msg_id]

    def put(self, msg_id):
        args = msg_put_args.parse_args()
        messages[msg_id] = args
        return messages[msg_id], 201


api.add_resource(Message, "/message/<int:msg_id>")

if __name__ == "__main__":
    app.run(debug=True)
