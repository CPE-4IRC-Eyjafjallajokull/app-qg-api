# RabbitMQ (aio-pika) quick use

Use the shared connection from `get_rabbitmq_connection` and publish/consume as needed.

```python
import json
import aio_pika
from fastapi import APIRouter, Depends

from app.api.dependencies import get_rabbitmq_connection

router = APIRouter()


@router.post("/publish")
async def publish_message(
    payload: dict, conn: aio_pika.abc.AbstractRobustConnection = Depends(get_rabbitmq_connection)
):
    channel = await conn.channel()
    await channel.default_exchange.publish(
        aio_pika.Message(body=json.dumps(payload).encode()),
        routing_key="sample.queue",
    )
    return {"status": "queued"}
```

Basic consumer pattern (run in a background task or startup hook):

```python
async def consume(conn: aio_pika.abc.AbstractRobustConnection):
    channel = await conn.channel()
    queue = await channel.declare_queue("sample.queue", durable=True)

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                print("got", message.body)
```
