from datetime import datetime, timedelta
import random

# Test 5s/10s/15s/30s timeframes
print("Testing 5s/10s/15s/30s timeframes:")
print("=" * 50)

for i in range(5):
    # Simulate current time
    current = datetime.now()
    
    # 10-20 seconds delay
    trade_delay = random.randint(10, 20)
    trade_time = current + timedelta(seconds=trade_delay)
    
    print(f"Test {i+1}:")
    print(f"  Current Time: {current.strftime('%H:%M:%S')}")
    print(f"  Delay: {trade_delay} seconds")
    print(f"  Trade Time: {trade_time.strftime('%H:%M:%S')}")
    print()

print("\nTesting 1M/2M/5M timeframes:")
print("=" * 50)

for i in range(5):
    current_time = datetime.now()
    minutes_delay = random.randint(1, 3)
    next_minute = (current_time + timedelta(minutes=1)).replace(second=0, microsecond=0)
    trade_time = next_minute + timedelta(minutes=minutes_delay - 1)
    
    print(f"Test {i+1}:")
    print(f"  Current Time: {current_time.strftime('%H:%M:%S')}")
    print(f"  Delay: {minutes_delay} minutes")
    print(f"  Trade Time: {trade_time.strftime('%H:%M:%S')}")
    print()
