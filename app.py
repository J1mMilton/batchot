from flask import Flask, render_template, request, session,jsonify
import openai
from dotenv import load_dotenv
import os
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

load_dotenv()

os.environ["http_proxy"] = "http://localhost:33210"
os.environ["https_proxy"] = "http://localhost:33210"
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY4")

store = {}
first = True

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

app = Flask(__name__)
app.secret_key = 'secretkey'  # Replace with your secret key

@app.route("/")
def index():
    global first
    store.clear()  # Clear the session when a new conversation starts
    first = True
    return render_template('chat.html')

@app.route("/get", methods=["GET", "POST"])
def chat():
    global store;
    global first;
    if first:
        welcome_message = 'Hello! Please type something and I will correct your grammar mistakes.'
        first = False
        return welcome_message
    prompt = """\
You are an English Grammar Detector. Your task is to correct grammar and spelling mistakes in the original input that is delimited by triple backticks. Follow these specific rules:\
1. Correct Mistakes: Identify and correct any grammar or spelling mistakes in the input. Do not change the meaning of the original input.\
After the correction, you surround each word you corrected with **.\
2. Normalize Case: Ensure proper capitalization (e.g., capitalize the first letter of sentences and proper nouns).\
3. You only output the final string.
Original input: ```{text}```
"""
    llm_model = "gpt-3.5-turbo"
    chatbot = ChatOpenAI(temperature=0.0, model=llm_model)
    prompt_template = ChatPromptTemplate.from_template(prompt)
    msg = request.form["msg"]
    input = msg
    user_messages = prompt_template.format_messages(text=input)
    with_message_history = RunnableWithMessageHistory(chatbot, get_session_history)
    config = {"configurable": {"session_id": "demo"}}
    response = with_message_history.invoke(user_messages, config=config)
    return str(response.content)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)