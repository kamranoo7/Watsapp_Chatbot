from flask import Flask, request, jsonify
import requests
import fitz  # PyMuPDF
import openai

app = Flask(__name__)

openai.api_key = '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'

# Load and extract text from PDF
def load_pdf_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

pdf_text = load_pdf_text("./gus_live_usage - Sheet1.pdf")

user_modes = {}  # Tracks whether the user is in GPT mode or PDF mode

def search_in_pdf(query, pdf_text, max_length=200):
    start = pdf_text.lower().find(query.lower())
    if start == -1:
        return "Sorry, I couldn't find information on that topic."
    end = start + max_length
    return pdf_text[start:end] + "..."

import traceback

def query_gpt(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": prompt}],
        )
        return response.choices[0].message['content'].strip()
    except openai.error.OpenAIError as e:
        print(f"OpenAI API error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()
    return "I'm having trouble processing your request right now."


@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        incoming_message = request.json
        try:
            sender_number = incoming_message['entry'][0]['changes'][0]['value']['messages'][0]['from']
            message_text = incoming_message['entry'][0]['changes'][0]['value']['messages'][0]['text']['body'].lower()

            # Check for mode toggle commands
            if message_text == "start gpt":
                user_modes[sender_number] = "GPT"
                response_text = "GPT mode activated. You can now ask me anything."
            elif message_text == "end gpt":
                user_modes[sender_number] = "PDF"
                response_text = "GPT mode deactivated."
            elif user_modes.get(sender_number) == "GPT":
                # Respond using GPT-3.5-turbo
                response_text = query_gpt(message_text)
            else:
                # Default to PDF search for responses
                if message_text in ['hi', 'hey', 'hello']:
                    response_text = "Hey, welcome to Capria. How may I help you?"
                else:
                    response_text = search_in_pdf(message_text, pdf_text)

            send_whatsapp_message(to=sender_number, message=response_text)
        except KeyError as e:
            print(f"Error parsing incoming message: {e}")
        return jsonify(success=True), 200

# send_whatsapp_message function remains the same




def send_whatsapp_message(to, message):
    url = "https://graph.facebook.com/v18.0/233232389874980/messages"
    headers = {
        'Authorization': 'Bearer EAAQCw46knDUBOxBNQJ4TmI9la4omy2qUAnsyZChcv8wPXx2aCFVavGgUiX7HHzZAaf9UqPSBZC2ufX0doZBFJEAMR3XfqgRBGWezsidStahMtQvp9amUvZAsu5dpcL2CH0pjmcogFSLrgu8grEkpxBWoD5Qv0uc3jHqeJZBAhxYZAHWWrJTtrMsijrQ1j0Q7qXItODDJ1DaIF4L1a4IrSMZD',  # Replace YOUR_ACCESS_TOKEN with your actual access token
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
