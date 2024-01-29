import os
import asyncio
import json
import logging
import torch
import websockets
import asyncio
import threading
from transformers import BertTokenizerFast, EncoderDecoderModel
from torch.multiprocessing import set_start_method, Queue, Process

logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
)

device = 'cuda' if torch.cuda.is_available() else 'cpu'
ckpt = 'mrm8488/bert2bert_shared-spanish-finetuned-summarization'
tokenizer = BertTokenizerFast.from_pretrained(ckpt)
model = EncoderDecoderModel.from_pretrained(ckpt).to(device)
logging.info("Initialized logger")


def generate_response(message):
    (text, identifier) = message
    print(f"starting summarization process")
    summarization = generate_summary(text)
    return {"value": summarization,"typ": "text" , "identifier": identifier}

# AI function
def generate_summary(text):
   inputs = tokenizer([text], padding="max_length", truncation=True, max_length=512, return_tensors="pt")
   input_ids = inputs.input_ids.to(device)
   attention_mask = inputs.attention_mask.to(device)
   output = model.generate(input_ids, attention_mask=attention_mask)
   return tokenizer.decode(output[0], skip_special_tokens=True)


async def callback(websocket, message):
    response = generate_response(message)
    logging.info(f"I received the message {response}")
    await websocket.send(json.dumps(response))

def between_callback(websocket, message):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(callback(websocket, message))
    loop.close()

global buffer
buffer = ""
global thread
thread = None
# Handle incoming messages
async def handle_message(websocket, path):
    async for message in websocket:
        global buffer
        global thread
        parsed = json.loads(message)
        text = parsed['value']
        buffer += text
        size_buffer = len(buffer)

        logging.info(f"Buffer {buffer}")
        if size_buffer != 0 and size_buffer > 10 and (thread == None or not thread.is_alive()):
            logging.info("Running background thread!!!")
            thread = threading.Thread(target=between_callback, args=(websocket, (buffer, parsed['identifier']),))
            thread.start()

        #between_callback(websocket, message)
        # response = generate_response(message)
        # logging.info(f"I received the message {response}")
        # await websocket.send(json.dumps(response))


# Start the WebSocket server
host = os.environ.get("SERVER_HOST_WS", "0.0.0.0")
port = int(os.environ.get("SERVER_PORT_WS", 8765))
start_server = websockets.serve(handle_message, host, port)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

