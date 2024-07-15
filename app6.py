import os
import re
import difflib
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
.cut {
    color: LightCoral;
    text-decoration: line-through;
}

.add {
    font-weight: bold;
    color: LightGreen;
}
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

def remove_prefix(text):
    return re.sub(r'^[\w\s]+:\s*', '', text)

# Function to replace markdown with HTML tags using regular expressions
def replace_markdown(text, marker, css_class):
    pattern = re.escape(marker) + '(.*?)' + re.escape(marker)
    replacement = rf"<span class='{css_class}'>\1</span>"
    return re.sub(pattern, replacement, text)

# Function to process message content
def process_message_content(content):
    # Replace ** for bold text
    content = replace_markdown(content, "**", "cut")
    # Replace ## for header text
    content = replace_markdown(content, "##", "add")
    return content

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if 'state' not in st.session_state:
    st.session_state['state'] = 'ask_task'

def reset_state():
    st.session_state['state'] = 'ask_task'

def on_user_input():
    current_state = st.session_state['state']

    if current_state == 'ask_task':
        task = st.session_state['task']
        st.session_state['state'] = 'choose_topic'

    elif current_state == 'choose_topic':
        topic = st.session_state['topic']
        st.session_state['state'] = 'provide_sentence'

    elif current_state == 'provide_sentence':
        st.session_state['state'] = 'user_input'

    elif current_state == 'user_input':
        user_response = st.session_state['user_input']
        st.session_state['state'] = 'provide_feedback'

    elif current_state == 'provide_feedback':
        reset_state()  # Start over or end

def get_background(query, chat_history):
    llm_model = "gpt-3.5-turbo"
    prompt = """
        You are an IELTS practice assistant. There are three stages of your replying process.
        1. You first ask what the user want to practice regarding IELTS writing.
        2. Then you ask what topic they want to practice.
        3. Then you provide a short example of what the users want to practice.
        If you have the information of a stage, you can go to the next stage.
        
        Chat history: {chat_history}
        User input: {user_input}
    """
    template = ChatPromptTemplate.from_template(prompt)
    llm = ChatOpenAI(temperature=0, model=llm_model)
    chain = template | llm | StrOutputParser()

    return chain.stream({
        "chat_history": chat_history,
        "user_input": query
    })

# get response
def get_response(query):

    llm_model = "gpt-3.5-turbo"
    llm = ChatOpenAI(temperature=0.7, model=llm_model)

    first_prompt = ChatPromptTemplate.from_template(
        "If input starts with keyword 'Fix Grammar: ', fix all the grammatical mistakes in the input."
        "If input starts with keyword 'Proofread: ', proofread the input."
        "If input starts with keyword 'Natural: ', modify the input so that it sounds more natural (maybe more casual and natural vocabulary or sentence structure)."
        "If input starts with keyword 'Improve: ', improve the language quality of the input (maybe using different vocabulary)."
        "If input starts with keyword 'Rewrite: ', rewrite the input content using better vocabulary and sentence structures, but don't change the overall meaning too much."
        "If none of the above, do what the user asks in the beginning of the input."
        "Only output the actual final content."
        "\n\n{input}"
    )
    chain_one = LLMChain(llm=llm, prompt=first_prompt,
                         output_key="improved"
                         )
    second_prompt = ChatPromptTemplate.from_template(
        "Compare input and improved, give an explanation in Chinese of how the grammar and vocabulary improved from input to improved."
        "The output starts with '\n\n'"
        "\n\n input: {input}"
        "\n\n improved: {improved}"
    )
    chain_two = LLMChain(llm=llm, prompt=second_prompt,
                         output_key="explain"
                         )

    overall_chain = SequentialChain(
        chains=[chain_one, chain_two],
        input_variables=["input"],
        output_variables=["improved", "explain"],
        verbose=True
    )

    response = overall_chain(query)

    original = remove_prefix(query)
    improved = response.get("improved")

    # Tokenize texts
    tokens1 = re.findall(r'\w+|[^\w\s]', original, re.UNICODE)
    tokens2 = re.findall(r'\w+|[^\w\s]', improved, re.UNICODE)

    # Create a Differ object
    differ = difflib.Differ()

    # Generate a comparison
    diff = list(differ.compare(tokens1, tokens2))

    # for d in diff:
    #     print(repr(d))

    # Prepare highlighted output
    styled_text = ""
    for token in diff:
        if token.startswith("+ "):
            styled_text += f"<span class='add'>{token[2:]}</span> "
        elif token.startswith("- "):
            styled_text += f"<span class='cut'>{token[2:]}</span> "
        elif not token.startswith('? '): # This line filters out the caret lines
            # Only add unchanged tokens directly
            styled_text += token[2:] + " "

    combined_text = styled_text + response.get("explain")

    for text in combined_text:
        yield text

def select():

    if st.session_state['state'] == 'ask_task':
        task = st.radio("What part of the task would you like to practice?", ("First paragraph", "Middle paragraph", "Last paragraph"))
        st.session_state['task'] = task
        user_query = st.chat_input("Which paragraph do you like to practice?")
        if user_query is None:
            if st.button("Next"):
                    user_query = task
                    st.session_state['state'] = 'choose_topic'
                    chat_1(user_query)
        else:
            st.session_state['state'] = 'choose_topic'
            chat_1(user_query)

    elif st.session_state['state'] == 'choose_topic':
        topic = st.selectbox("Choose your topic:", ["Environment", "Technology", "Education"])
        st.session_state['topic'] = topic
        user_query = st.chat_input("What topic would you like to practice?")
        if user_query is None:
            if st.button("Next"):
                    user_query = topic
                    st.session_state['state'] = 'provide_feedback'
                    chat_1(user_query)
        else:
            st.session_state['state'] = 'provide_feedback'
            chat_1(user_query)
    elif st.session_state['state'] == 'provide_feedback':
        user_query = st.chat_input("Say something!!")
        print(user_query)
        chat_2(user_query)

if not st.session_state.chat_history:
    st.session_state.chat_history.append(AIMessage("Hello! I can help you with your IELTS writing Task 2! 😎"))

# conversation
for message in st.session_state.chat_history:
    if isinstance(message, HumanMessage):
        with st.chat_message("Human", avatar="🤓"):
            st.markdown(process_message_content(message.content), unsafe_allow_html=True)
    else:
        with st.chat_message("AI", avatar="👽"):
            st.markdown(process_message_content(message.content), unsafe_allow_html=True)

# user_query = st.chat_input("Say something!!")
# st.session_state['input'] = user_query

def chat_1(user_query):
    if user_query is not None and user_query != "":
        st.session_state.chat_history.append(HumanMessage(user_query))

        with st.chat_message("Human", avatar="🤓"):
            processed_query = process_message_content(user_query)
            st.markdown(processed_query, unsafe_allow_html=True)

        with st.chat_message("AI", avatar="👽"):
            ai_response = st.write_stream(get_background(user_query, st.session_state.chat_history))

        st.session_state.chat_history.append(AIMessage(ai_response))
        st.rerun()

def chat_2(user_query):
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

        st.session_state.chat_history.append(AIMessage(ai_response))
        st.rerun()

select()
if st.button("reset", type = "primary"):
    reset_state()
    st.rerun()