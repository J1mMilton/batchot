from flask import Flask, render_template, request, session
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
        session['chat_messages'] = [{'role': 'system', 'content': '### Instructions ###\
You are an English Grammar Detector. Your task is to correct grammar and spelling mistakes in the user\'s input. Follow these specific rules:\
1. Correct Mistakes: Identify and correct any grammar or spelling mistakes. Do not forget the original input.\
Do not change the meaning of the original input.\
2. Highlight Corrections: Compare the corrected input and the original input,\
and find their different words in terms of subjects, verbs, objects, or compliments.\
Surround each different word you find with `**`.\
3. Normalize Case: Ensure proper capitalization (e.g., capitalize the first letter of sentences and proper nouns).\
4. Please do not forget to highlight any words.\
### Examples ###\
# Input: "I goes to the market." Output: "I **went** to the market."\
# Input: "The apple was very juicy." Output: "The apple was very juicy."\
# Input: "He buyed a new book." Output: "He **bought** a new book."\
# Input: "The Apples are red." Output: "The apples are red."\
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
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=1000  # Limit the response length
        )

        response = completion.choices[0].message.content
        session['chat_messages'].append({'role': 'assistant', 'content': response})
        session.modified = True  # Mark the session as modified so it gets saved

        return response
    except Exception as e:
        app.logger.error(f"Error connecting to OpenAI API: {e}")
        return "There was an error connecting to the OpenAI API."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)