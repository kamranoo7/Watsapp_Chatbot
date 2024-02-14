from flask import Flask, request, jsonify
import requests
import traceback
import weaviate
from datetime import datetime
import time
from flask_cors import CORS
import openai
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
CORS(app)
# name="Capria1"
# cname="Capria1"
# Assuming your API keys and tokens are now stored securely
import openai

# Assuming your API keys are stored securely and are now being correctly retrieved
key = "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"

# Set the API key
openai.api_key = key
import os

key = os.getenv('KEY')
whatsapp_token = os.getenv('WHATSAPP_TOKEN')
weaviate_api_key = os.getenv('WEAVIATE_API_KEY')
weaviate_url = os.getenv('WEAVIATE_URL')

# Now you can use the openai module to make API calls


lm_client = openai.OpenAI(api_key=key)
whatsapp_token = "YOUR_WHATSAPP_TOKEN"

import weaviate




# Correct initialization for Weaviate client with API key
# Note: The exact method will depend on the version of the Weaviate client library and the authentication mechanism it supports.

# If your version of the Weaviate client supports direct API key usage, it would typically look something like this:
db_client = weaviate.Client(
    url="https://murrkfdqk2cac91dqye6w.c0.us-west1.gcp.weaviate.cloud",
    auth_client_secret=weaviate.AuthApiKey(api_key="37ESFfEpfIn6Csis9by0Cdq9WQl91AEP9kpY"),
    additional_headers={"X-OpenAI-Api-Key": key}
)

user_nodes={}

def qdb(query, db_client, name, cname):
    context = None
    metadata = []
    try:
        limit = 5
        res = (
            db_client.query.get(name, ["text", "metadata"])
            .with_near_text({"concepts": query})
            .with_limit(limit)
            .do()
        )
        context = ""
        metadata = []
        chunk_id = 0
        for i in range(limit):
            context += "Chunk ID: " + str(chunk_id) + "\n"
            context += res["data"]["Get"][cname][i]["text"] + "\n\n"
            print("context111111111111111111111111111111111111",context)
            metadata.append(res["data"]["Get"][cname][i]["metadata"])
            chunk_id += 1
    except Exception as e:
        print("Exception in DB, dude.")
        print(e)
        time.sleep(3)
        context, metadata = qdb(query, db_client, name, cname)
        print(context,"contextxtttttttt")
    return context, metadata



def generate_chat_response(user_question, context):
    # Construct the system and user messages
    print("context222222222222",context)
    system_message = "Given below is a piece of text about Capria. You will be asked questions about it. Please do answer only using the information given below. take your time, and read it carefully and thoroughly. Do not miss anything. The information might be in a non-contiguous unstructured manner. Do not use our own information. Think carefully and provide detailed and long answers. The person asking the question does not know about the context, please answer directly. I am retrieving the below chunks from a vector DB. Before each chunk, I am providing the modification date. Whenever you are confused, pick the information from the chunk which contains the more recent modification date. There will be a lot of conflicting information. Use the modification date to pick recent information. The current date is: October 28th, 2023. If you are unable to generate a response from the context, return 'Unanswerable question':   \n" + context
    user_message = f"Question: {user_question} Additional context and instructions for the LLM"
    # print("context222222222222",context)
    # Prepare the messages payload for the LLM
    msg = [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': user_message}
    ]
    


    print(msg,"the message is here ")
    # Function to call the OpenAI API
    def call_api():
          # Assuming lm_client is the OpenAI client initialized globally
        response = lm_client.chat.completions.create(
            model="gpt-4",
            messages=msg,
            max_tokens=1000,
            temperature=0.0
        )
        # Extract the LLM's response
        return response.choices[0].message.content

    # Call the API and get the response
    try:
        reply = call_api()
        print("LLM Response:", reply)
        return reply
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return None

# This function takes the user's question and any relevant context, then communicates with the LLM to get a response. It abstracts away details like error handling and thread management for simplicity.

import logging

logging.basicConfig(level=logging.INFO)

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    logging.info("Received a request")
    if request.method == 'GET':
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if verify_token == '123456':
            return challenge
        else:
            return 'Verification token mismatch', 403
    if request.method == 'POST':
        incoming_message = request.json
        logging.info(f"Incoming message: {incoming_message}")
        try:
            # Check if 'messages' key exists
            if 'messages' in incoming_message['entry'][0]['changes'][0]['value']:
                sender_number = incoming_message['entry'][0]['changes'][0]['value']['messages'][0]['from']
                message_text = incoming_message['entry'][0]['changes'][0]['value']['messages'][0]['text']['body'].lower()
                context = qdb(message_text, db_client, "Capria1", "Capria1")
                print("contextttttttttttttttttttttttttttttttttttttt",context)
                response_text = generate_chat_response(message_text, context[0])
                print("Response Text...............................",response_text)
                send_whatsapp_message(sender_number, response_text)
            else:
                print("No 'messages' key in the incoming message.")
        except KeyError as e:
            print(f"Error parsing incoming message: {e}")
        except Exception as e:
            print(f"Unhandled exception: {e}")
            # Handle the case where sender_number is not defined due to the exception
            # send_whatsapp_message(sender_number, "Sorry, an error occurred while processing your request.")
            
        return jsonify(success=True), 200


def send_whatsapp_message(to, message):
    url = "https://graph.facebook.com/v18.0/233232389874980/messages"
    headers = {
        'Authorization': 'Bearer EAAQCw46knDUBOyONs7rMVA3YQhUU8AsPrKoEQIZBF1Hy3OtwsZAJuwgS3JJsYw4qbQFVhVVjBbtxH7ucS4C6iYUoqkmqlztvbHIFZA9Vv1SrZAPjRAMvWPNFpqsdLYReSxDTCcOtuFyteR2YotnMITt7ZCs0wA6ViV1UNbOW8hoMHJsTeP7OOASnplwy7nsRSPiATZA3XlRiy6zsR0LBwZD',  # Replace YOUR_ACCESS_TOKEN with your actual access token
        'Content-Type': 'application/json'
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": message
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print("Message sent successfully")
    else:
        print("Failed to send message", response.text)

if __name__ == '__main__':
    app.run(debug=True)