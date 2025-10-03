import streamlit as st
from langgraph_backend import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage
import uuid

def generate_thread_id():
    return str(uuid.uuid4())

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    # Placeholder for loading conversation logic
    # In a real application, you would load from a database or file
    return chatbot.get_state(config={"configurable": {'thread_id': thread_id}}).values.get('messages', [])

def get_thread_display_name(thread_id):
    """Generate a user-friendly name for a thread"""
    messages = load_conversation(thread_id)
    
    if messages and len(messages) > 0:
        # Get the first user message to create a preview
        first_user_msg = None
        for msg in messages:
            if isinstance(msg, HumanMessage):
                first_user_msg = msg.content
                break
        
        if first_user_msg:
            # Take first 30 characters and clean it up
            preview = first_user_msg.strip()[:30]
            if len(first_user_msg) > 30:
                preview += "..."
            return f"💬 {preview}"
    
    # Fallback to thread ID with chat icon
    return f"💬 Chat {thread_id[:8]}"

# st.session_state -> dict -> doesn't get erased on rerun

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()

add_thread(st.session_state['thread_id'])

st.sidebar.title("LangGraph Chatbot")
if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("My Conversations")

for thread_id in st.session_state['chat_threads'][::-1]:
    display_name = get_thread_display_name(thread_id)
    if st.sidebar.button(display_name, key=thread_id):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []

        for message in messages:
            if(isinstance(message, HumanMessage)):
                role = 'user'
            else:
                role = 'assistant'
            temp_messages.append({'role': role, 'content': message.content})
        
        st.session_state['message_history'] = temp_messages

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

# {'role': 'user', 'content':'Hi'}

user_input = st.chat_input('Type your message here...')

if user_input:

    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    

    with st.chat_message('user'):
        st.text(user_input)

    CONFIG = {"configurable": {'thread_id': st.session_state['thread_id']}}

    # Call your backend here
    # response = chatbot.invoke({'messages': [HumanMessage(content=user_input)]}, config=CONFIG)
    # ai_message = response['messages'][-1].content

    with st.chat_message('assistant'):
        ai_message = st.write_stream(
            message_chunk.content for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            )
        )
    

    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})