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
You are an English Grammar Detector. Your task is to correct grammatical and spelling mistakes in the original input that is delimited by triple backticks. Follow these specific rules:\
1. Do not confuse grammatical mistakes with spelling mistakes. You first correct the spelling mistakes, then the grammatical mistakes. \
2. This step is very important, never forget this. When you are correcting and only correcting a spelling mistake, you surround the corrected word with ##. \
3. This step is very important, never forget this. When you are correcting and only correcting a grammatical mistake, you surround the corrected word with **. \
4. Normalize Case: Ensure proper capitalization (e.g., capitalize the first letter of sentences and proper nouns).\
5. You generate only the final output in the first paragraph (don't include the string "the final output"), then in the second paragraph you generate only a Chinese explanation of the mistakes in the original input.\
6. There must be a line break between the first and the second paragraph.\
7. Example: from "Nice meet you. i'm olld enough" to "Nice **to** meet you. I'm ##old## enough".
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