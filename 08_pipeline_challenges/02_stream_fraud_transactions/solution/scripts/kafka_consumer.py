from kafka import KafkaConsumer
import pandas as pd
import json
import time
from collections import defaultdict

# Kafka Configuration
KAFKA_BROKER = "localhost:9092"
TOPIC_NAME = "fraud-transactions"

# Store transaction history for users
USER_TRANSACTION_HISTORY = defaultdict(list)

# Define thresholds
TRANSACTION_THRESHOLD = 5  # Number of transactions
TIME_WINDOW = 60           # Time window in seconds

def generate_flags(transaction):
    """
    Analyze a transaction and generate flags for suspicious activity.

    Flags include:
    - high_amount: Transaction amount exceeds $10,000.
    - rapid_transactions: User makes more than 5 transactions in 60 seconds.
    - suspicious_location: Transaction occurs outside the user's home city.
    """
    flags = []
    user_id = transaction['user_id']

    # Flag high transaction amounts
    if transaction['transaction_amount'] > 10000:
        flags.append('high_amount')

    # Track user transactions for high-frequency detection
    current_time = time.time()
    USER_TRANSACTION_HISTORY[user_id].append(current_time)

    # Remove old transactions outside the time window
    USER_TRANSACTION_HISTORY[user_id] = [
        t for t in USER_TRANSACTION_HISTORY[user_id] if current_time - t <= TIME_WINDOW
    ]

    # Debugging: Log the number of recent transactions for this user
    print(f"User {user_id} has {len(USER_TRANSACTION_HISTORY[user_id])} transactions in the last {TIME_WINDOW} seconds.")

    # Flag high-frequency transactions
    if len(USER_TRANSACTION_HISTORY[user_id]) > TRANSACTION_THRESHOLD:
        flags.append('rapid_transactions')

    # Flag transactions outside the home city
    home_city = transaction['home_city']['city']
    transaction_city = transaction['location']['city']
    if transaction_city != home_city:
        flags.append('suspicious_location')

    # Add a timestamp for processing
    transaction['processed_at'] = time.strftime("%Y-%m-%d %H:%M:%S")

    return flags

# Function to process a transaction
def process_transaction(transaction):
    """Process and flag a transaction."""
    flags = generate_flags(transaction)
    transaction['flags'] = flags  # Add flags as a column
    return transaction


# Function to save data to CSV
def save_to_csv(data, filename):
    """Save processed transactions to a CSV file."""
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Saved {len(data)} transactions to {filename}")


def consume_from_kafka():
    """
    Consume transactions from Kafka, process them, and save to CSV.

    Transactions are flagged for suspicious activity and saved in two files:
    - processed_transactions.csv: All transactions (flagged and unflagged).
    - flagged_transactions.csv: Only transactions with flags.

    Saves data in batches of 100 transactions for efficiency.
    """
    consumer = KafkaConsumer(
        TOPIC_NAME,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",  # Start processing from the earliest message
        enable_auto_commit=True,
        group_id="fraud-consumer-group"
    )

    processed_data = []
    flagged_data = []  # Track flagged transactions
    batch_size = 100
    transactions_since_last_save = 0

    print("Kafka consumer started. Waiting for messages...")
    try:
        for message in consumer:
            try:
                transaction = message.value
                print(f"Received Transaction: {transaction}")

                # Process transaction and track flagged transactions
                processed_transaction = process_transaction(transaction)
                processed_data.append(processed_transaction)
                transactions_since_last_save += 1

                if processed_transaction['flags']:
                    flagged_data.append(processed_transaction)

                print(f"Processed Transaction: {json.dumps(processed_transaction, indent=2)}")
            except Exception as e:
                print(f"Error processing transaction: {e}")

            # Save data to CSV after processing batch_size transactions
            if transactions_since_last_save >= batch_size:
                save_to_csv(processed_data, "processed_transactions.csv")
                save_to_csv(flagged_data, "flagged_transactions.csv")
                transactions_since_last_save = 0
    
    except KeyboardInterrupt:
        print("Consumer stopped.")
        save_to_csv(processed_data, "processed_transactions.csv")
        save_to_csv(flagged_data, "flagged_transactions.csv")
    finally:
        consumer.close()

if __name__ == "__main__":
    consume_from_kafka()
