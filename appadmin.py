import streamlit as st
from streamlit_chat import message
from langchain.prompts import (
    PromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain_core.output_parsers import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, Tool
from pymongo import MongoClient
from datetime import datetime
import random
import requests
from langchain.tools import Tool
import hashlib
import mysql.connector
from datetime import datetime
import random
import pandas as pd;
from collections import Counter
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="vaibhav@1507",  # Replace with your MySQL password
        database="complaints_db"
    )
conn = get_db_connection()  
cursor = conn.cursor() 
# Function to authenticate users
def authenticate_user(username, password, role):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        hashed_password = hash_password(password)
        query = "SELECT * FROM users WHERE username = %s AND password_hash = %s AND role = %s"
        cursor.execute(query, (username, hashed_password, role))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user is not None  # Returns True if user exists, False otherwise
    except Exception as e:
        print(f"Error during authentication: {e}")
        return False


# Establish database connection
 # Use the connection to create a cursor



######
st.set_page_config(page_title="AI Chatbot", page_icon="🤖", layout="centered")

# Simulated user database (username: hashed_password)
# users_db = {"testuser": hashlib.sha256("mypassword".encode()).hexdigest()}

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to authenticate users


# Function to register users
def register_user(username, password, role):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    if cursor.fetchone():  # Check if user already exists
        return False
    password_hash = hash_password(password)
    cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)", (username, password_hash, role))
    conn.commit()
    cursor.close()
    conn.close()
    return True

def assign_complaint(complaint_id, department):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE complaints SET department = %s WHERE id = %s", (department, complaint_id))
        conn.commit()
        
        return True
    except Exception as e:
        st.error(f"Error assigning department: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""
##############
login_type = st.radio("Login as:", ["User", "Admin"])

#### MongoDB Connection ####
# MONGO_CONNECTION_STRING = "mongodb+srv://sakshamjain0464:mypwd123@cluster0.rqeb3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
# DB_NAME = "Chatbot"

#### Google Gemini API Key ####
API_KEY = "AIzaSyBkDv8qzti3aBbfYD-d6lpa2g_NnSN_vnA"

chat_model = ChatGoogleGenerativeAI(
    api_key=API_KEY, model="gemini-1.5-flash", temperature=0.6
)

#### Prompt Template ####
basic_prompt = """You are GwaliorMitra, a helpful chatbot for Smart City Gwalior. Answer only questions related to Gwalior.
If the question is unrelated, say "I don't know with an apology." Provide responses in markdown format.

### Topics you can answer:
1. **City Heritage and Culture**
2. **Infrastructure and Transportation**
3. **Climate and Geography**
4. **Economy and Industry**
5. **Education and Healthcare**
6. **Tourism and Attractions**
7. **Food and Restaurants**

### Complaint System:
1. **Register a Complaint** (Get complaint ID)
2. **Check Complaint Status** (Using complaint ID)
3. **Categorize Complaint** (Choose category)
4. **Escalate Complaint** (Mark as escalated)

## Categories:
- **Traffic** (signals, congestion, parking)
- **Infrastructure** (roads, buildings)
- **Public Health** (sanitation, garbage)
- **Utilities** (electricity, water)
- **Safety** (crime, law enforcement)
- **Environment** (pollution, wildlife)
- **Public Transport** (buses, trains)
- **Education** (schools, colleges)
- **Healthcare** (hospitals, emergency services)
- **Civic Amenities** (parks, libraries)

**Question**: {question}
**Context**: {context}
"""

system_prompt = SystemMessagePromptTemplate(
    prompt=PromptTemplate(input_variables=["context"], template=basic_prompt)
)
human_prompt = HumanMessagePromptTemplate(
    prompt=PromptTemplate(input_variables=["question"], template="{question}")
)
messages = [system_prompt, human_prompt]
prompt_template = ChatPromptTemplate(input_variables=["context", "question"], messages=messages)

#### Conversation History ####
conversation_history = []

if "complaints" not in st.session_state:
    st.session_state.complaints = []

#### Complaint Registration Function ####
cursor = conn.cursor()
def fetch_complaints():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # Ensure proper cursor type
        
        cursor.execute("SELECT * FROM complaints")
        complaints = cursor.fetchall()
        
        return pd.DataFrame(complaints)  # Convert to DataFrame
    except Exception as e:
        st.error(f"Error fetching complaints: {e}")
        return pd.DataFrame()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def handle_register_complaint(complaint):
    try:
        now = datetime.now()
        complaint_id = random.randint(1000, 9999)

        query = "INSERT INTO complaints (id, complaint, date, status, resolved) VALUES (%s, %s, %s, %s, %s)"
        values = (complaint_id, complaint, now.strftime("%Y-%m-%d"), "pending", False)

        cursor.execute(query, values)
        conn.commit()  # Save changes in database

        return str(complaint_id)  # Return the complaint ID
    except Exception as e:
        print(e)
        return "Try Again"


#### Get Complaints Function ####
def handle_get_complaints(input_data=None):  
    try:
        cursor.execute("SELECT * FROM complaints")
        complaints = cursor.fetchall()  # Fetch all complaints from the table

        complaints_list = []
        for row in complaints:
            complaints_list.append({
                "id": row[0],
                "complaint": row[1],
                "date": row[2],
                "status": row[3],
                "resolved": row[4]
            })

        return complaints_list
    except Exception as e:
        print(e)
        return []


#### Get Local News Function ####
def get_news(number):
    try:
        url = "0d9480cb15e64f8badfd7b6db6798ba8"
        querystring = {"query": "Gwalior", "country": "IN", "lang": "en", "limit": number}
        response = requests.get(url, params=querystring)
        return response.json().get('data', "No news found")
    except Exception as e:
        return f"Error fetching news: {e}"
def update_complaint_status(complaint_id, new_status):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE complaints SET status = %s WHERE id = %s", (new_status, complaint_id))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error updating status: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
#### Define Tools for Agent ####
tools = [
    Tool(name="info", func=lambda x: chat_model.invoke(x), description="Provides city information."),
    Tool(name="Register Complaint", func=handle_register_complaint, description="Registers complaints."),
    Tool(name="Get Complaints", func=handle_get_complaints, description="Retrieves all complaints."),
    Tool(name="news", func=get_news, description="Fetches latest Gwalior news.")
]

#### Initialize AI Agent ####
agent = initialize_agent(
    tools=tools,
    llm=chat_model,
    agent="zero-shot-react-description",
    verbose=True,
    max_iterations=5,  # Prevents infinite loops
    max_execution_time=10,  # Stops long-running queries
    handle_parsing_errors="raise"  # Debugs AI output issues
)

# Streamlit UI
st.title("Login Page")

if not st.session_state.logged_in:
    menu = ["Login", "Register"] if login_type == "User" else ["Admin Login"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Login":
        st.subheader("User Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if authenticate_user(username, password, "user"):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = "user"
                st.success(f"Welcome {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password")

    elif choice == "Register":
        st.subheader("Register as User")
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        if st.button("Register"):
            if register_user(new_username, new_password, "user"):
                st.success("User registered successfully! You can now log in.")
            else:
                st.error("Username already exists. Try a different one.")

    elif choice == "Admin Login":
        st.subheader("Admin Login")
        admin_username = st.text_input("Admin Username")
        admin_password = st.text_input("Admin Password", type="password")
        if st.button("Login as Admin"):
            if authenticate_user(admin_username, admin_password, "admin"):
                st.session_state.logged_in = True
                st.session_state.username = admin_username
                st.session_state.role = "admin"
                st.success("Admin access granted!")
                st.rerun()
            else:
                st.error("Invalid admin credentials")
# Ensure chat history is initialized before any conditional check
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [{"role": "chatbot", "content": "Hey, how can I help you today?"}]

# If logged in, show user or admin interface
else:
    if st.session_state.role == "user":
        st.title("Janta-Vaani")
        st.write("An AI-powered complaint system for Smart City Gwalior.")

        # Display chat messages
        for i, chat in enumerate(st.session_state.chat_history):
            message(chat["content"], is_user=(chat["role"] == "user"), key=f"chat_{i}")

        # User input field
        user_input = st.text_input("Type your message:", key="user_input")

        if st.button("Send") and user_input.strip():
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            combined_context = "\n".join(
                [c["content"] for c in st.session_state.chat_history if c["role"] == "chatbot"]
            )

            now = datetime.now()
            current_date = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M")

            # Generate AI response
            response = agent.run(
                f"Context: {combined_context}\nQuestion: {user_input}\nCurrent Date: {current_date} Current Time: {current_time}"
            )

            # Add chatbot response to chat history
            st.session_state.chat_history.append({"role": "chatbot", "content": response})
            st.rerun()

    if st.session_state.role == "admin":
        # 🚀 **Admin Dashboard**
        st.title("Municipal Complaint Management - Admin Dashboard")
        st.success(f"Logged in as {st.session_state.username} (Admin)")

        # Load Complaints Data
        complaints_df = fetch_complaints()

        # Filters
        st.sidebar.header("Filter Complaints")
        status_filter = st.sidebar.selectbox("Filter by Status", ["All"] + complaints_df["status"].unique().tolist())
        category_filter = st.sidebar.selectbox("Filter by Category", ["All"] + complaints_df["category"].unique().tolist())
        priority_filter = st.sidebar.selectbox("Filter by Priority", ["All"] + complaints_df["priority"].unique().tolist())

        # Apply Filters
        filtered_df = complaints_df.copy()
        if status_filter != "All":
            filtered_df = filtered_df[filtered_df["status"] == status_filter]
        if category_filter != "All":
            filtered_df = filtered_df[filtered_df["category"] == category_filter]
        if priority_filter != "All":
            filtered_df = filtered_df[filtered_df["priority"] == priority_filter]

        st.subheader("Complaints List")
        st.dataframe(filtered_df)

        # Assign Department
        st.subheader("Assign Complaints to Departments")
        complaint_id = st.selectbox("Select Complaint ID", complaints_df["id"].tolist())
        department = st.selectbox("Assign to Department", ["Sanitation", "Water Department", "Traffic Control", "Health Services","Police","Crime Branch","Animal Welfare Board","Public work department"])

        if st.button("Assign"):
            if assign_complaint(complaint_id, department):
                st.success(f"Complaint {complaint_id} assigned to {department}")
                st.rerun()
       #update the status
        st.subheader("Change Complaint Status")
        if not complaints_df.empty:
          complaint_id = st.selectbox("Select Complaint ID", complaints_df["id"].tolist(), key="status_complaint_id")
          new_status = st.selectbox("Select New Status", ["pending", "in progress", "resolved", "escalated"], key="status_new_status")

        if st.button("Update Status", key="update_status_btn"):
           if update_complaint_status(complaint_id, new_status):
              st.success(f"Complaint {complaint_id} status updated to {new_status}")
              st.rerun()
        else:
         st.warning("No complaints available.")


         # Analytics
        st.subheader("Analytics and Trends")
        if not complaints_df.empty:
            most_common_category = Counter(complaints_df["category"]).most_common(1)[0][0]
            st.metric(label="Most Common Complaint Category", value=most_common_category)

            status_counts = complaints_df["status"].value_counts()
            st.bar_chart(status_counts)

        st.write("This dashboard helps administrators manage complaints efficiently by tracking, filtering, and assigning them to appropriate departments.")

