import asyncio
import json
import os
import nats
from nats.errors import ConnectionClosedError, TimeoutError, NoServersError
from fastapi import FastAPI
from pydantic import BaseModel

# NATS client setup
nc = None

app = FastAPI(title="Orders Service", version="1.0.0")

async def nats_event_handler(msg):
    """
    This is our async event listener. It gets called whenever a message
    arrives on the subscribed subject.
    """
    subject = msg.subject
    data = msg.data.decode()
    
    print(f"Received message on subject '{subject}': {data}")
    
    try:
        event = json.loads(data)
        event_type = event.get("event_type")
        event_data = event.get("data")
        
        if event_type == "product.created":
            # Process the event here
            product_id = event_data.get("id")
            product_name = event_data.get("name")
            print(f"Processing event: New product '{product_name}' (ID: {product_id}) was created.")
            
            # Simulate some processing, like creating a new order item or logging
            # to a database. In a real-world scenario, this would be a complex
            # business logic function.
            await asyncio.sleep(1)
            print(f"✅ Finished processing product creation for ID: {product_id}")
            
    except json.JSONDecodeError:
        print(f"Error decoding JSON: {data}")
    except Exception as e:
        print(f"An error occurred during event processing: {e}")

@app.on_event("startup")
async def startup_event():
    """Connect to NATS and start the event listener on startup."""
    global nc
    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    try:
        nc = await nats.connect(servers=[nats_url])
        print("Connected to NATS server.")
        
        # Subscribe to the 'product.created' subject.
        # This is how the service listens for events.
        await nc.subscribe("product.created", cb=nats_event_handler)
        print("Subscribed to 'product.created' subject.")

    except Exception as e:
        print(f"Could not connect to NATS: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Disconnect from NATS on shutdown."""
    if nc and not nc.is_closed:
        await nc.close()
        print("Disconnected from NATS server.")

@app.get("/")
async def root():
    return {"message": "Welcome to the Orders Service"}