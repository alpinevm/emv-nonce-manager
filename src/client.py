import os
from os.path import dirname, join
import json

import redis
from dotenv import load_dotenv
from redis.client import PubSub

load_dotenv(join(dirname(__file__), '..' , '.env'))

NUM_REQUESTS: int = 10
# Connect to the Redis queue
redis_client: redis.Redis = redis.from_url(os.environ["REDIS_URL"])
queue: str = 'ethereum_transaction_queue'
receiver_address: str = "0x5eE49779dC4bd4CA802660678a8E3F57FB5f4a2b"

def get_subscribed_channel(channel_id: str) -> PubSub:
    pubsub: PubSub = redis_client.pubsub()
    pubsub.subscribe(channel_id)
    return pubsub
     
def add_transaction_to_queue(address: str, channel_id: str) -> str:
  # Serialize the transaction and add it to the queue
    queue_payload: dict = {
        "address": address,
        "channel_id": channel_id 
    }
    redis_client.rpush(queue, json.dumps(queue_payload))
    return channel_id 


channel_ids: list[str] = [os.urandom(32).hex() for _ in range(NUM_REQUESTS)]
# Subscribe before we send our txns, just in case we get a fast response
subscribed_channels: list[PubSub] = list(map(get_subscribed_channel, channel_ids))
list(map(add_transaction_to_queue, [receiver_address]*NUM_REQUESTS, channel_ids))
print("Transactions sent, waiting...")

# Listen for messages on the channel
received: int = 0
while received < NUM_REQUESTS:
    for channel in subscribed_channels:
        message = channel.get_message()
        if message:
            if message['type'] == "message" and (message["data"].decode("utf-8") == "success" or message["data"].decode("utf-8") == "failure"):
                received += 1
                print(f"Responded with {message['data']}")
                print(f"{NUM_REQUESTS-received} left to handle")
