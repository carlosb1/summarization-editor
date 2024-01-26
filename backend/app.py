import os
import asyncio
import json
import logging
import torch
import websockets
from transformers import BertTokenizerFast, EncoderDecoderModel
from torch.multiprocessing import set_start_method, Queue, Process

logging.basicConfig(
    format="%(message)s",
    level=logging.DEBUG,
)

device = 'cuda' if torch.cuda.is_available() else 'cpu'
ckpt = 'mrm8488/bert2bert_shared-spanish-finetuned-summarization'
tokenizer = BertTokenizerFast.from_pretrained(ckpt)
model = EncoderDecoderModel.from_pretrained(ckpt).to(device)
logging.info("Initialized logger")

def generate_response(new_content):
    parsed = json.loads(new_content)
    text = parsed['value']
    identifier = parsed['identifier']
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

# Handle incoming messages
async def handle_message(websocket, path):
    async for message in websocket:
        response = generate_response(message)
        logging.info(f"I received the message {response}")
        await websocket.send(json.dumps(response))


# Start the WebSocket server
host = os.environ.get("SERVER_HOST_WS", "0.0.0.0")
port = int(os.environ.get("SERVER_PORT_WS", 8765))
start_server = websockets.serve(handle_message, host, port)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

