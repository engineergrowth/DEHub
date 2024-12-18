from kafka import KafkaProducer
import json
import random
import time
import uuid

KAFKA_BROKER = "localhost:9092"
TOPIC_NAME = "fraud-transactions"

# List of cities
CITIES = [
    {"city": "New York", "lat": 40.7128, "lon": -74.0060},
    {"city": "San Francisco", "lat": 37.7749, "lon": -122.4194},
    {"city": "Chicago", "lat": 41.8781, "lon": -87.6298},
    {"city": "London", "lat": 51.5074, "lon": -0.1278}
]

# Predefined set of user IDs
USER_IDS = [str(uuid.uuid4()) for _ in range(100)]  # Simulate 100 unique users
USER_PROFILES = {user_id: random.choice(CITIES) for user_id in USER_IDS}  # Assign a home city to each user


def generate_random_location(home_city):
    """
    Return a random location for the transaction.

    80% of the time, the location matches the user's home city.
    20% of the time, a random city is selected to simulate travel.
    """
    if random.random() < 0.8:
        return home_city
    else:
        travel_city = random.choice(CITIES)
        while travel_city == home_city:
            travel_city = random.choice(CITIES)
        return travel_city


def generate_transaction():
    """
    Generate a realistic transaction for a randomly selected user.

    Includes fields such as user ID, transaction amount, location,
    home city, device ID, and timestamp.
    """
    user_id = random.choice(USER_IDS)  # Pick a random user
    home_city = USER_PROFILES[user_id]  # Get the user's home city
    location = generate_random_location(home_city)  # Determine the transaction location

    transaction = {
        "user_id": user_id,
        "transaction_amount": round(random.uniform(5.00, 20000.00), 2),
        "location": location,
        "home_city": home_city,
        "device_id": str(uuid.uuid4()),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    return transaction


def send_to_kafka():
    """
    Continuously generate and send transactions to a Kafka topic.

    Transactions simulate real-world data and are sent at random intervals
    to the specified Kafka topic.
    """
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    print("Starting Kafka producer. Press Ctrl+C to stop.")
    try:
        while True:
            transaction = generate_transaction()
            producer.send(TOPIC_NAME, transaction)
            print(f"Sent: {transaction}")
            time.sleep(random.uniform(0.5, 2))  # Simulate random intervals
    except KeyboardInterrupt:
        print("Producer stopped.")
    finally:
        producer.close()


if __name__ == "__main__":
    send_to_kafka()
