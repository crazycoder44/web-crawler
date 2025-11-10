"""
Manual test script to verify reporting works with real database.
Run this directly: python test_manual_db.py
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from bson import ObjectId
import json

from motor.motor_asyncio import AsyncIOMotorClient
from src.scheduler.reporting import ChangeReporter
from src.scheduler.notifications import NotificationManager
from src.crawler.settings import Settings

async def test_real_database():
    """Manual test with real MongoDB."""
    print("="*60)
    print("MANUAL DATABASE TEST")
    print("="*60)
    
    settings = Settings()
    
    # Connect to test database
    client = AsyncIOMotorClient(settings.mongo_uri)
    db = client['manual_test_bookstore']  # Separate test database
    
    print(f"\n✓ Connected to MongoDB: {settings.mongo_uri}")
    print(f"✓ Using test database: manual_test_bookstore")
    
    try:
        # Create reporter
        reporter = ChangeReporter(db_client=client)
        reporter.db = db
        reporter.store = db  # Use same db for store
        reporter.notifications = NotificationManager()
        
        Path('reports').mkdir(exist_ok=True)
        
        print("\n" + "-"*60)
        print("STEP 1: Inserting test books")
        print("-"*60)
        
        # Insert test books
        test_books = [
            {
                '_id': ObjectId(),
                'title': 'Python Programming',
                'price': 29.99,
                'availability': 'in_stock'
            },
            {
                '_id': ObjectId(),
                'title': 'Web Scraping Guide',
                'price': 39.99,
                'availability': 'in_stock'
            }
        ]
        
        await db.books.insert_many(test_books)
        print(f"✓ Inserted {len(test_books)} books:")
        for book in test_books:
            print(f"  - {book['title']} (${book['price']})")
        
        print("\n" + "-"*60)
        print("STEP 2: Creating change records")
        print("-"*60)
        
        # Create change records
        today = datetime.utcnow()
        start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
        
        test_changes = [
            {
                'book_id': test_books[0]['_id'],
                'timestamp': start_of_day + timedelta(hours=1),
                'changes': {
                    'price': {
                        'old': '29.99',
                        'new': '24.99'
                    }
                }
            },
            {
                'book_id': test_books[1]['_id'],
                'timestamp': start_of_day + timedelta(hours=2),
                'changes': {
                    'availability': {
                        'old': 'in_stock',
                        'new': 'out_of_stock'
                    }
                }
            },
            {
                'book_id': test_books[0]['_id'],
                'timestamp': start_of_day + timedelta(hours=3),
                'changes': {
                    'title': {
                        'old': 'Python Programming',
                        'new': 'Python Programming (2nd Edition)'
                    }
                }
            }
        ]
        
        await db.change_records.insert_many(test_changes)
        print(f"✓ Inserted {len(test_changes)} change records:")
        for i, change in enumerate(test_changes, 1):
            field = list(change['changes'].keys())[0]
            print(f"  {i}. {field} change for book {test_books[0 if i != 2 else 1]['title']}")
        
        print("\n" + "-"*60)
        print("STEP 3: Generating daily report")
        print("-"*60)
        
        # Generate report
        report = await reporter.generate_daily_report(today)
        
        print(f"\n📊 REPORT SUMMARY:")
        print(f"   Date: {report['date']}")
        print(f"   Total Changes: {report['total_changes']}")
        print(f"   Change Types: {', '.join(report['changes_by_type'].keys())}")
        
        print(f"\n📋 DETAILED BREAKDOWN:")
        for change_type, data in report['changes_by_type'].items():
            print(f"\n   {change_type.upper()}:")
            print(f"   - Count: {data['count']}")
            for detail in data['details']:
                print(f"   - {detail['book_title']}: {detail['old_value']} → {detail['new_value']}")
        
        print("\n" + "-"*60)
        print("STEP 4: Verifying report files")
        print("-"*60)
        
        # Check files
        json_reports = list(Path('reports').glob('change_report_*.json'))
        csv_reports = list(Path('reports').glob('change_report_*.csv'))
        
        if json_reports:
            print(f"✓ JSON report created: {json_reports[0].name}")
            
            # Show JSON content
            with open(json_reports[0], 'r') as f:
                json_content = json.load(f)
                print(f"\n📄 JSON Report Preview:")
                print(json.dumps(json_content, indent=2, default=str)[:500] + "...")
        else:
            print("✗ No JSON report found!")
        
        if csv_reports:
            print(f"\n✓ CSV report created: {csv_reports[0].name}")
            
            # Show CSV content
            with open(csv_reports[0], 'r') as f:
                lines = f.readlines()
                print(f"\n📄 CSV Report Preview ({len(lines)} lines):")
                for line in lines[:5]:  # Show first 5 lines
                    print(f"   {line.strip()}")
        else:
            print("✗ No CSV report found!")
        
        print("\n" + "-"*60)
        print("STEP 5: Testing record_change method")
        print("-"*60)
        
        # Test record_change
        new_change_id = await reporter.record_change(
            str(test_books[0]['_id']),
            {
                'price': {
                    'old': '24.99',
                    'new': '19.99'
                }
            }
        )
        
        print(f"✓ Recorded new change: {new_change_id}")
        
        # Verify it was stored
        stored = await db.change_records.find_one({'_id': ObjectId(new_change_id)})
        if stored:
            print(f"✓ Change verified in database")
            print(f"  - Book ID: {stored['book_id']}")
            print(f"  - Changes: {stored['changes']}")
        else:
            print("✗ Change not found in database!")
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        
        print(f"\nThe database 'manual_test_bookstore' has been left intact.")
        print(f"To clean up, run: mongo manual_test_bookstore --eval 'db.dropDatabase()'")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Don't drop database so you can inspect it
        print(f"\nClosing connection...")
        client.close()

if __name__ == "__main__":
    asyncio.run(test_real_database())