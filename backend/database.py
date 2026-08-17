import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI not found in .env file. Please check your .env setup.")

client = MongoClient(MONGO_URI)

db = client["linkedinpost_db"]

users_collection = db["users"]
history_collection = db["history"]


def test_connection():
    try:
        client.admin.command("ping")
        print("✅ MongoDB connection successful!")
    except Exception as e:
        print("❌ MongoDB connection failed:", e)


if __name__ == "__main__":
    test_connection()