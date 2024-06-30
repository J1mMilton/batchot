from flask import Flask, render_template, request, jsonify, session
from openai import OpenAI
from dotenv import load_dotenv
import os

#os.environ["http_proxy"] = "http://localhost:33210"
#os.environ["https_proxy"] = "http://localhost:33210"

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
You first greet the user, then present your teaching style, \
and then asks them to pick a style from them. \
You wait to collect the user’s need, then start teaching in that manner \
If user wants to quit, you ask for their feedback on the service you’ve provided. \
Finally you say “adios” to the user.\
Make sure to clarify all options\
identify the teaching styles from the knowledgebase.\
users have to choose a specific style,\
you are not teaching them if they don\'t choose from your specific styles. \
You will stand your ground and refuse their proposal, forcing them to choose one style \
You respond in a very professional but friendly way, splitting your message and \
your corrections. \
The knowledgebase includes \
1. Dialogue and Conversation \
2. Professional English \
3. Correction of every mistake \
'}]
        welcome_message = 'Hello! Welcome to our English tutoring session. I am Markus, your English tutor. Before we begin, I want to share with you my teaching style options. \
        You can choose from the following: \
        1. Dialogue and Conversation: We focus on practicing conversations and everyday English dialogues. \
        2. Professional English: We work on formal and business English skills. \
        3. Correction of every mistake: I will point out and explain every mistake you make in your English. \
        Please choose a style that best suits your needs, and we can start our session from there.'
        session['chat_messages'].append({'role': 'assistant', 'content': welcome_message})
        session.modified = True  # Mark the session as modified so it gets saved
        return jsonify({'msg': welcome_message})

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

    return jsonify({'msg': response})

    # If the user made a grammatical mistake, correct them
    # if 'correction' in response:
    #     correction, explanation = response.split('\n')
    #     return jsonify({'msg': correction, 'explanation': explanation})

    # return jsonify({'msg': response})

if __name__ == '__main__':
    app.run(debug=True)