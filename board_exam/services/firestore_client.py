import firebase_admin
from firebase_admin import credentials, firestore, storage

if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()

    firebase_admin.initialize_app(cred, {
        'storageBucket': 'project-5e6fa15a-0ef4-476a-b87.firebasestorage.app'
    })

db = firestore.client()
bucket = storage.bucket()