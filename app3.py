import os
import re
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
import json

load_dotenv()

os.environ["http_proxy"] = "http://localhost:33210"
os.environ["https_proxy"] = "http://localhost:33210"
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY4")

st.set_page_config(page_title="SURF Chatbot", page_icon="🤖")

st.title("SURF Chatbot")

custom_css = """
<style>
.grammar {
    font-weight: bold;
    color: tomato;
    text-decoration: underline;
}

.spelling {
    font-weight: bold;
    color: deepskyblue;
}
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

# Function to replace markdown with HTML tags using regular expressions
def replace_markdown(text, marker, css_class):
    pattern = re.escape(marker) + '(.*?)' + re.escape(marker)
    replacement = rf"<span class='{css_class}'>\1</span>"
    return re.sub(pattern, replacement, text)

# Function to process message content
def process_message_content(content):
    # Replace ** for bold text
    content = replace_markdown(content, "**", "grammar")
    # Replace ## for header text
    content = replace_markdown(content, "##", "spelling")
    return content

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if not st.session_state.chat_history:
    st.session_state.chat_history.append(AIMessage("Hello! I can generate charts! 🤖"))

# get response
def get_response(query):
    prompt = """\
You are a data analyst. Your task is to translate the description in the original input to data.
The original input is delimited by triple backticks. Follow these specific rules:\
1. If relevant data for a chart is mentioned, include it in JSON format under a line "Data for chart:".\
Original input: ```{text}```
"""
    prompt_template = ChatPromptTemplate.from_template(prompt)
    llm_model = "gpt-3.5-turbo"
    chatbot = ChatOpenAI(temperature=0.0, model=llm_model)
    chain = prompt_template | chatbot | StrOutputParser()

    return chain.stream({
        "text": query
    })


# Function to generate a chart from data
def generate_chart(data):
    df = pd.DataFrame(data)
    st.line_chart(df)

# Function to detect and process chart commands
def detect_chart_command(response_content):
    chart_data = None
    collecting = False
    json_string = ""  # Initialize an empty string to collect JSON data
    lines = response_content.split('\n')

    for line in lines:
        if collecting:
            json_string += line.strip()  # Add current line to JSON string
            if line.strip().endswith('}'):  # Check if this line ends the JSON object
                try:
                    chart_data = json.loads(json_string)
                    break  # If successful, exit the loop
                except json.JSONDecodeError:
                    st.error(f"Failed to parse chart data. Data received: '{json_string}'")
                    json_string = ""  # Reset JSON string in case of failure
                    collecting = False  # Stop collecting
                    continue

        if line.startswith("Data for chart:"):
            collecting = True  # Start collecting lines for JSON

    if not chart_data and collecting:  # If no data was parsed but we started collecting
        st.error(f"Failed to complete parsing of chart data. Partial data: '{json_string}'")

    if chart_data:
        generate_chart(chart_data)

    if not collecting:
        st.error("No 'Data for chart:' line found in the response.")



# conversation
for message in st.session_state.chat_history:
    if isinstance(message, HumanMessage):
        with st.chat_message("Human", avatar="🤓"):
            st.markdown(process_message_content(message.content), unsafe_allow_html=True)
    else:
        with st.chat_message("AI", avatar="👽"):
            st.markdown(process_message_content(message.content), unsafe_allow_html=True)

user_query = st.chat_input("Say something!!")
if user_query is not None and user_query != "":
    st.session_state.chat_history.append(HumanMessage(user_query))

    with st.chat_message("Human", avatar="🤓"):
        processed_query = process_message_content(user_query)
        st.markdown(processed_query, unsafe_allow_html=True)

    with st.chat_message("AI", avatar="👽"):
        response_placeholder = st.empty()
        ai_response = ""
        for partial_response in get_response(user_query):  # Assuming get_response is a generator
            ai_response += partial_response
            processed_response = process_message_content(ai_response)
            response_placeholder.markdown(processed_response, unsafe_allow_html=True)

        detect_chart_command(ai_response)

    st.session_state.chat_history.append(AIMessage(ai_response))
