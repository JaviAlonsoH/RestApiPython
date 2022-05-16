from models.models import User

def authenticate(username, password):
    print("authenticate")
    user = User.objects(username=username).first()
    if user_manager.verify_password(password, user):
        return user


def identity(payload):
    print("identity")
    user_id = payload['identity']
    print(user_id)
    user= User.objects(id=user_id).first()
    return user


