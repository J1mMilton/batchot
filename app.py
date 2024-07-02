from flask import Flask, render_template, request, jsonify, session
from openai import OpenAI
from dotenv import load_dotenv
import os

os.environ["http_proxy"] = "http://localhost:33210"
os.environ["https_proxy"] = "http://localhost:33210"

load_dotenv()

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY4'),  # Access the API key from environment variable
)

# print(client.api_key)

app = Flask(__name__)
app.secret_key = 'secretkey'  # Replace with your secret key

@app.route("/")
def index():
    session.clear()  # Clear the session when a new conversation starts
    return render_template('chat.html')

@app.route("/get", methods=["GET", "POST"])
def chat():
    if 'chat_messages' not in session:
        session['chat_messages'] = [{'role': 'system', 'content': 'You are Markus, a super patient English tutor that has a lot of experience teaching non-native speakers. \
You will correct and only correct the grammar mistakes from user\'s input.\
Make the letter cases normal.\
The mistaken part of the sentence should be in the format of <span style="color:red">corrected parts</span>.\
'}]
        welcome_message = 'Hello! Please type something and I will correct your grammar mistakes.'
        session['chat_messages'].append({'role': 'assistant', 'content': welcome_message})
        session.modified = True  # Mark the session as modified so it gets saved
        return welcome_message

    msg = request.form["msg"]
    input = msg
    session['chat_messages'].append({'role': 'user', 'content': input})
    session.modified = True  # Mark the session as modified so it gets saved
    return get_openai_response(session['chat_messages'])

def get_openai_response(messages):
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=150  # Limit the response length
    )

    response = completion.choices[0].message.content
    session['chat_messages'].append({'role': 'assistant', 'content': response})
    session.modified = True  # Mark the session as modified so it gets saved

    return response

if __name__ == '__main__':
    app.run(debug=True)