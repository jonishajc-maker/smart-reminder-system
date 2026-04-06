# -----------------------------
# SMART REMINDER SYSTEM (FINAL VERSION WITHOUT spaCy)
# Streamlit UI + User Control + Keyword-based Date Parsing
# -----------------------------

import streamlit as st
import sqlite3
from datetime import datetime, timedelta
from dateutil import parser as dateparser
from sklearn.tree import DecisionTreeClassifier

# -----------------------------
# Database
# -----------------------------
conn = sqlite3.connect("reminders.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task TEXT,
    due_date TEXT,
    category TEXT,
    priority TEXT,
    done INTEGER DEFAULT 0
)
""")
conn.commit()

# -----------------------------
# ML Model (optional use)
# -----------------------------
CATEGORIES = {"assignment": 0, "work": 1, "event": 2, "other": 3}
X_train = [[2,0],[6,0],[12,0],[48,1],[72,1],[2,2],[80,2],[3,3],[100,3]]
y_train = [1,1,1,0,0,1,0,1,0]
clf = DecisionTreeClassifier(max_depth=3)
clf.fit(X_train, y_train)

# -----------------------------
# Keyword-based Date Extraction
# -----------------------------
DATE_KEYWORDS = ["today", "tomorrow", "next", "by", "on", "at", "before", "due"]

def extract_reminder(text):
    words = text.split()
    date_words = []
    task_words = []
    for w in words:
        lw = w.lower().strip('.,!?')
        if lw in DATE_KEYWORDS:
            date_words.append(lw)
        else:
            task_words.append(w)
    task = ' '.join(task_words) or text

    due_date = None
    date_str = ' '.join(date_words)
    if date_str:
        try:
            due_date = dateparser.parse(date_str, default=datetime.now())
        except:
            pass

    return task, due_date

# -----------------------------
# Predict Priority
# -----------------------------

def predict_priority(due_date, category):
    if due_date is None:
        return "Optional"
    hours = (due_date - datetime.now()).total_seconds()/3600
    cat_id = CATEGORIES.get(category, 3)
    result = clf.predict([[hours, cat_id]])[0]
    return "Critical" if result == 1 else "Optional"

# -----------------------------
# Add Reminder
# -----------------------------
def add_reminder(task, due_date, category, priority):
    due_str = due_date.strftime("%Y-%m-%d %H:%M") if due_date else "No date"
    cursor.execute("INSERT INTO reminders (task, due_date, category, priority) VALUES (?,?,?,?)",
                   (task, due_str, category, priority))
    conn.commit()

# -----------------------------
# Get Reminders
# -----------------------------
def get_reminders():
    cursor.execute("SELECT * FROM reminders ORDER BY due_date")
    return cursor.fetchall()

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="AI Smart Assistant", page_icon="📅", layout="wide")
st.title("🎓 AI Smart Student Assistant")
st.markdown("### More control. More clarity. No forced decisions.")

menu = st.sidebar.radio("Navigation", [
    "Add Reminder",
    "View Reminders",
    "Mark Done",
    "Delete Reminder"
])

# -----------------------------
# ADD REMINDER
# -----------------------------
if menu == "Add Reminder":
    st.subheader("➕ Add New Reminder")
    text = st.text_input("Enter your task (natural language allowed)")

    auto_extract = st.checkbox("Auto-detect date using keywords")
    extracted_date = None
    if auto_extract and text:
        task_only, extracted_date = extract_reminder(text)
        if extracted_date:
            st.success(f"Detected date: {extracted_date}")
        else:
            task_only = text
    else:
        task_only = text

    col1, col2 = st.columns(2)
    with col1:
        manual_date = st.datetime_input("Or choose date manually", value=datetime.now())
    with col2:
        category = st.selectbox("Category", ["assignment", "work", "event", "other"])

    priority_mode = st.radio("Priority Mode", ["Auto (AI decides)", "Manual (You choose)"])

    if priority_mode == "Manual (You choose)":
        priority = st.selectbox("Select Priority", ["Critical", "Optional"])
    else:
        chosen_date = extracted_date if extracted_date else manual_date
        priority = predict_priority(chosen_date, category)
        st.info(f"AI Suggested Priority: {priority}")

    if st.button("Add Reminder"):
        final_date = extracted_date if extracted_date else manual_date
        add_reminder(task_only, final_date, category, priority)
        st.success("Reminder Added Successfully!")

# -----------------------------
# VIEW REMINDERS
# -----------------------------
elif menu == "View Reminders":
    st.subheader("📋 Your Reminders")
    data = get_reminders()
    if not data:
        st.warning("No reminders yet.")
    else:
        for r in data:
            color = "🔴" if r[4] == "Critical" else "🟢"
            done = "✅" if r[5] else "❌"
            st.markdown(f"""{color} **{r[1]}**  
📅 {r[2]} | 📂 {r[3]} | {done}""")

# -----------------------------
# MARK DONE
# -----------------------------
elif menu == "Mark Done":
    st.subheader("✔ Mark Reminder as Done")
    data = get_reminders()
    ids = [r[0] for r in data]
    if ids:
        selected = st.selectbox("Select ID", ids)
        if st.button("Mark Done"):
            cursor.execute("UPDATE reminders SET done=1 WHERE id=?", (selected,))
            conn.commit()
            st.success("Marked as done")

# -----------------------------
# DELETE
# -----------------------------
elif menu == "Delete Reminder":
    st.subheader("🗑 Delete Reminder")
    data = get_reminders()
    ids = [r[0] for r in data]
    if ids:
        selected = st.selectbox("Select ID", ids)
        if st.button("Delete"):
            cursor.execute("DELETE FROM reminders WHERE id=?", (selected,))
            conn.commit()
            st.success("Deleted successfully")
