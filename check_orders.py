from pymongo import MongoClient
from datetime import datetime, timedelta

client = MongoClient('mongodb://localhost:27017')
db = client['canteenDB']
orders = db['orders']

print("=" * 50)
print("CANTEEN DATABASE - ORDERS REPORT")
print("=" * 50)

# Total orders
total = orders.count_documents({})
print(f"\n📊 Total Orders: {total}")

# Today's orders
today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
today_orders = 0
yesterday_orders = 0

for order in orders.find({}):
    created_at = order.get('created_at')
    if created_at:
        if isinstance(created_at, datetime):
            if created_at.date() == today.date():
                today_orders += 1
            elif created_at.date() == (today - timedelta(days=1)).date():
                yesterday_orders += 1

print(f"📅 Today's Orders: {today_orders}")
print(f"📅 Yesterday's Orders: {yesterday_orders}")

# Status wise
print("\n📋 Orders by Status:")
statuses = ['pending', 'confirmed', 'preparing', 'ready', 'delivered']
for status in statuses:
    count = orders.count_documents({'status': status})
    if count > 0:
        print(f"   {status.upper()}: {count}")

# All orders details
print("\n🛒 All Orders Details:")
print("-" * 70)
for order in orders.find({}, {'_id': 0}):
    order_id = order.get('id', 'N/A')
    customer = order.get('customer_name', 'N/A')
    status = order.get('status', 'N/A')
    created_at = order.get('created_at', 'N/A')
    amount = order.get('total_amount', 0)
    
    if created_at and isinstance(created_at, datetime):
        date_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
    else:
        date_str = str(created_at)[:19] if created_at else 'N/A'
    
    print(f"   #{order_id:<6} | {customer:<20} | {status.upper():<10} | ₹{amount:<8} | {date_str}")

print("\n" + "=" * 50)
print("MongoDB Compass Check:")
print("   Database: canteenDB")
print("   Collection: orders")
print("=" * 50)

client.close()
