"""Fix checkpoint index issue"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def fix_index():
    client = AsyncIOMotorClient('mongodb://localhost:27017/books')
    db = client.get_default_database()
    
    try:
        # Drop the problematic unique index
        await db.checkpoints.drop_index('unique_checkpoint_type')
        print("✅ Dropped problematic unique index on checkpoint_type")
    except Exception as e:
        print(f"Note: {e}")
    
    # Delete checkpoint documents with null checkpoint_type
    result = await db.checkpoints.delete_many({'checkpoint_type': None})
    print(f"✅ Deleted {result.deleted_count} checkpoint documents with null checkpoint_type")
    
    client.close()
    print("✅ Database cleanup complete")

if __name__ == "__main__":
    asyncio.run(fix_index())
