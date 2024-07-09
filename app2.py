import os
import re
import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain.chains import SequentialChain
from langchain.chains import LLMChain
from langchain.chains import SimpleSequentialChain

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

# get response
def get_response(query):

    llm_model = "gpt-3.5-turbo"
    llm = ChatOpenAI(temperature=0.0, model=llm_model)

    first_prompt = ChatPromptTemplate.from_template(
        "Fix all the mistakes in the input. If you changed a word, you surround the corrected word with **."
        "\n\n{para}"
    )
    chain_one = LLMChain(llm=llm, prompt=first_prompt,
                         output_key="para2"
                         )
    second_prompt = ChatPromptTemplate.from_template(
        "Keep the original **s in the input. Slightly improve the language of the input. Anytime you changed a word, you must surround the changed word with ##."
        "If and only if you changed a word inside two **s, you replace the two **s around that exact word with ##"
        "Don't change all the **s."
        "At least surround one word with ##."
        "\n\n{para2}"
    )
    chain_two = LLMChain(llm=llm, prompt=second_prompt,
                         output_key="para3"
                         )
    overall_chain = SequentialChain(
        chains=[chain_one, chain_two],
        input_variables=["para"],
        output_variables=["para3"],
        verbose=True
    )


    # chain = prompt_template | chatbot | StrOutputParser()

    for text in overall_chain(query).get("para3"):
        yield text

if not st.session_state.chat_history:
    st.session_state.chat_history.append(AIMessage("Hello! Please type something and I will correct your **grammatical** and ##spelling## mistakes.  \nI will also provide you with Chinese (中文) explanation!"))

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
        # response_placeholder = st.empty()
        # ai_response = ""
        # response = get_response(user_query)
        # for partial_response in response:
        #     ai_response += partial_response
        #     processed_response = process_message_content(ai_response)
        #     response_placeholder.markdown(processed_response, unsafe_allow_html=True)
        response_placeholder = st.empty()
        ai_response = ""
        for partial_response in get_response(user_query):  # Assuming get_response is a generator
            ai_response += partial_response
            processed_response = process_message_content(ai_response)
            response_placeholder.markdown(processed_response, unsafe_allow_html=True)

    st.session_state.chat_history.append(AIMessage(ai_response))





#     prompt = """\
# You are an English Grammar Detector. Your task is to correct grammatical and spelling mistakes in the original input that is delimited by triple backticks. Follow these specific rules:\
# 1. Do not confuse grammatical mistakes with spelling mistakes. You first correct the spelling mistakes, then the grammatical mistakes. \
# 2. This step is very important, never forget this. When you are correcting and only correcting a spelling mistake, you surround the corrected word with ##. \
# 3. This step is very important, never forget this. When you are correcting and only correcting a grammatical mistake, you surround the corrected word with **. \
# 4. Normalize Case: Ensure proper capitalization (e.g., capitalize the first letter of sentences and proper nouns).\
# 5. You generate only the final output in the first paragraph (don't include the string "the final output"), then in the second paragraph you generate only a Chinese explanation of the mistakes in the original input.\
# 6. Example: from "Nice meet you. i'm olld enough" to "Nice **to** meet you. I'm ##old## enough".
# Original input: ```{text}```
# """



