import streamlit as st
import sqlite3
import bcrypt
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os

# -----------------------
# Load ENV
# -----------------------
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="Secure Groq Chatbot", page_icon="🤖")

# -----------------------
# Database Setup
# -----------------------
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password BLOB
)
""")
conn.commit()

# -----------------------
# Helper Functions
# -----------------------
def create_user(username, password):
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
        return True
    except:
        return False

def verify_user(username, password):
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    if result:
        stored_pw = result[0]
        return bcrypt.checkpw(password.encode(), stored_pw)
    return False

# -----------------------
# Session States
# -----------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "messages" not in st.session_state:
    st.session_state.messages = []

if "page" not in st.session_state:
    st.session_state.page = "login"

# -----------------------
# Navigation
# -----------------------
def go_to_login():
    st.session_state.page = "login"

def go_to_signup():
    st.session_state.page = "signup"

def logout():
    st.session_state.logged_in = False
    st.session_state.messages = []
    st.session_state.page = "login"
    st.rerun()

# -----------------------
# SIGNUP PAGE
# -----------------------
if not st.session_state.logged_in and st.session_state.page == "signup":
    st.title("🆕 Create Account")

    new_user = st.text_input("Username")
    new_pass = st.text_input("Password", type="password")

    if st.button("Register"):
        if create_user(new_user, new_pass):
            st.success("Account created! Please login.")
            go_to_login()
        else:
            st.error("Username already exists!")

    st.button("Already have an account? Login", on_click=go_to_login)

# -----------------------
# LOGIN PAGE
# -----------------------
elif not st.session_state.logged_in:
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if verify_user(username, password):
            st.session_state.logged_in = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.button("Create new account", on_click=go_to_signup)

# -----------------------
# CHATBOT PAGE
# -----------------------
else:
    st.title("🤖 Groq Secure Chatbot")
    st.sidebar.button("Logout", on_click=logout)

    # Show chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_input = st.chat_input("Ask something...")

    if user_input:
        st.chat_message("user").markdown(user_input)
        st.session_state.messages.append(
            {"role": "user", "content": user_input}
        )

        llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.7,
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a helpful assistant."),
                ("user", "{question}")
            ]
        )

        chain = prompt | llm | StrOutputParser()

        response = chain.invoke({"question": user_input})

        with st.chat_message("assistant"):
            st.markdown(response)

        st.session_state.messages.append(
            {"role": "assistant", "content": response}
        )
