# import firebase_admin
# from firebase_admin import credentials

# def initialize_firebase():
#     if not firebase_admin._apps:
#         cred = credentials.ApplicationDefault()
#         firebase_admin.initialize_app(cred)
import firebase_admin
from firebase_admin import credentials, storage

def initialize_firebase():
    if not firebase_admin._apps:

        # Uses Cloud Run / local env credentials
        cred = credentials.ApplicationDefault()

        firebase_admin.initialize_app(cred, {
            'storageBucket': 'project-5e6fa15a-0ef4-476a-b87.firebasestorage.app'
        })


# initialize once
initialize_firebase()

# global bucket reference
bucket = storage.bucket()