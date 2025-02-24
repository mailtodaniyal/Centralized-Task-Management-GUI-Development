import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

conn = sqlite3.connect("tasks.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS clients (
    client_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    ip_address TEXT NOT NULL
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    due_date TEXT NOT NULL,
    client_id INTEGER,
    status TEXT NOT NULL DEFAULT 'Pending',
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
)
""")
conn.commit()

menu = st.sidebar.selectbox("Navigation", ["Admin Panel", "Client Panel"])

if menu == "Admin Panel":
    st.title("Admin Panel - Task Management")

    st.subheader("Manage Clients")
    client_name = st.text_input("Client Name")
    client_ip = st.text_input("Client IP Address")
    if st.button("Add Client"):
        cursor.execute("INSERT INTO clients (name, ip_address) VALUES (?, ?)", (client_name, client_ip))
        conn.commit()
        st.success("Client Added Successfully!")

    st.subheader("Existing Clients")
    clients = pd.read_sql("SELECT * FROM clients", conn)
    st.dataframe(clients)

    st.subheader("Assign Tasks")
    task_title = st.text_input("Task Title")
    task_due_date = st.date_input("Due Date")
    client_list = cursor.execute("SELECT client_id, name FROM clients").fetchall()
    client_dict = {name: client_id for client_id, name in client_list}
    assigned_client = st.selectbox("Assign to Client", options=client_dict.keys())

    if st.button("Assign Task"):
        cursor.execute("INSERT INTO tasks (title, due_date, client_id) VALUES (?, ?, ?)", 
                       (task_title, task_due_date.strftime('%Y-%m-%d'), client_dict[assigned_client]))
        conn.commit()
        st.success("Task Assigned Successfully!")

    st.subheader("All Tasks")
    tasks = pd.read_sql("""
        SELECT tasks.task_id, tasks.title, tasks.due_date, clients.name, tasks.status 
        FROM tasks 
        JOIN clients ON tasks.client_id = clients.client_id
    """, conn)
    st.dataframe(tasks)

elif menu == "Client Panel":
    st.title("Client Panel - View & Update Tasks")

    client_name = st.text_input("Enter Your Name to Login")
    if st.button("Login"):
        client_id = cursor.execute("SELECT client_id FROM clients WHERE name = ?", (client_name,)).fetchone()
        if client_id:
            st.session_state["client_id"] = client_id[0]
            st.success(f"Logged in as {client_name}")
        else:
            st.error("Client Not Found! Contact Admin.")

    if "client_id" in st.session_state:
        client_id = st.session_state["client_id"]
        st.subheader("Your Tasks")
        client_tasks = pd.read_sql("SELECT * FROM tasks WHERE client_id = ?", conn, params=(client_id,))
        for _, row in client_tasks.iterrows():
            st.write(f"**Task:** {row['title']} | **Due Date:** {row['due_date']} | **Status:** {row['status']}")
            new_status = st.selectbox(f"Update Status for Task {row['task_id']}", ["Pending", "In Progress", "Completed"], index=["Pending", "In Progress", "Completed"].index(row['status']))
            if st.button(f"Update Task {row['task_id']}"):
                cursor.execute("UPDATE tasks SET status = ? WHERE task_id = ?", (new_status, row['task_id']))
                conn.commit()
                st.success("Task Updated!")

st.sidebar.markdown("---")
st.sidebar.text("Task Management System")
