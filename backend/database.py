import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database management for MongoDB integration"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.users_collection = None
        self.sessions_collection = None
        self.logs_collection = None
        
    async def connect_to_database(self):
        """Connect to MongoDB database"""
        try:
            # Use MongoDB connection string from environment or default
            mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
            
            self.client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_url)
            self.db = self.client.vira_ai
            self.users_collection = self.db.users
            self.sessions_collection = self.db.sessions
            self.logs_collection = self.db.logs
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("Connected to MongoDB successfully")
            
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            # Continue without database - system will work with in-memory storage
    
    async def close_database(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")
    
    async def save_user_session(self, user_id: str, session_data: Dict[str, Any]):
        """Save user session data"""
        try:
            if self.sessions_collection:
                await self.sessions_collection.update_one(
                    {"user_id": user_id},
                    {"$set": session_data},
                    upsert=True
                )
        except Exception as e:
            logger.error(f"Error saving user session: {e}")
    
    async def get_user_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user session data"""
        try:
            if self.sessions_collection:
                session = await self.sessions_collection.find_one({"user_id": user_id})
                return session
            return None
        except Exception as e:
            logger.error(f"Error getting user session: {e}")
            return None
    
    async def log_interaction(self, user_id: str, message: str, response: str, metadata: Dict[str, Any] = None):
        """Log user interaction"""
        try:
            if self.logs_collection:
                log_entry = {
                    "user_id": user_id,
                    "message": message,
                    "response": response,
                    "timestamp": metadata.get("timestamp") if metadata else None,
                    "metadata": metadata or {}
                }
                await self.logs_collection.insert_one(log_entry)
        except Exception as e:
            logger.error(f"Error logging interaction: {e}")
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            if self.logs_collection:
                total_interactions = await self.logs_collection.count_documents({"user_id": user_id})
                last_interaction = await self.logs_collection.find_one(
                    {"user_id": user_id},
                    sort=[("timestamp", -1)]
                )
                
                return {
                    "total_interactions": total_interactions,
                    "last_interaction": last_interaction.get("timestamp") if last_interaction else None
                }
            return {"total_interactions": 0, "last_interaction": None}
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {"total_interactions": 0, "last_interaction": None}

# Global database instance
database = DatabaseManager()