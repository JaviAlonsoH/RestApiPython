import firebase_admin
from firebase_admin import credentials, storage

cred = credentials.Certificate("./serviceAccountKey.json")
firebase_app = firebase_admin.initialize_app(cred, {
    'storageBucket': 'https://console.firebase.google.com/project/tence-9d154/storage/tence-9d154.appspot.com/files'
})
bucket = storage.bucket('[object Blob]')