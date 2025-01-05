import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

class Database:
    client: Optional[AsyncIOMotorClient] = None
    
    # MongoDB connection details from environment variables
    MONGODB_URL = os.getenv('MONGODB_URL', "mongodb://mongo:UmxHXTOOXKBaiFQUnsawgcTQSmwkOHBw@autorack.proxy.rlwy.net:54479")
    DATABASE_NAME = os.getenv('DATABASE_NAME', "cursor3")

    @classmethod
    async def connect_db(cls):
        try:
            cls.client = AsyncIOMotorClient(cls.MONGODB_URL)
            # Verify connection
            await cls.client.admin.command('ping')
            print("Successfully connected to MongoDB!")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise

    @classmethod
    async def close_db(cls):
        if cls.client is not None:
            cls.client.close()
            print("MongoDB connection closed")

    @classmethod
    def get_db(cls):
        if cls.client is None:
            raise Exception("Database not initialized")
        return cls.client[cls.DATABASE_NAME]

    @classmethod
    async def create_indexes(cls):
        db = cls.get_db()
        try:
            await db.patients.create_index("id", unique=True)
            await db.patients.create_index("name.family")
            await db.patients.create_index("gender")
            await db.patients.create_index("birthDate")
            print("Database indexes created successfully")
        except Exception as e:
            print(f"Error creating indexes: {e}")
            raise