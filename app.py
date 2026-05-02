import streamlit as st
import pandas as pd
import sqlite3
import datetime
import os
import plotly.express as px
import plotly.graph_objects as go
import time

# --- INITIALIZATION & CONFIG ---
st.set_page_config(page_title="CollabSpace Pro", page_icon="🌌", layout="wide", initial_sidebar_state="expanded")

os.makedirs("data", exist_ok=True)
DB_FILE = "data/collab_pro.db"

# --- CUSTOM CSS ---
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    div[data-testid="stMetricValue"] { font-size: 2.2rem; font-weight: 700; color: #4dabf7; }
    div[data-testid="stMetricLabel"] { font-size: 1rem; color: #adb5bd; font-weight: 500; }
    
    .badge { padding: 4px 10px; border-radius: 12px; font-size: 0.75em; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    .badge-High { background-color: rgba(255, 75, 75, 0.2); color: #ff4b4b; border: 1px solid rgba(255, 75, 75, 0.5); }
    .badge-Medium { background-color: rgba(255, 170, 0, 0.2); color: #ffaa00; border: 1px solid rgba(255, 170, 0, 0.5); }
    .badge-Low { background-color: rgba(0, 200, 100, 0.2); color: #00c864; border: 1px solid rgba(0, 200, 100, 0.5); }
    
    .task-card {
        background-color: #1a1c23;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #2d303a;
        margin-bottom: 14px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .task-card:hover { transform: translateY(-2px); box-shadow: 0 8px 15px rgba(0,0,0,0.2); border-color: #4dabf7; }
    .task-title { font-weight: 600; font-size: 1.15em; margin-bottom: 8px; color: #f8f9fa; }
    .task-desc { font-size: 0.9em; color: #adb5bd; margin-bottom: 12px; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
    .task-meta { font-size: 0.85em; color: #868e96; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #2d303a; padding-top: 10px; }
    
    .kanban-header { padding: 12px; border-radius: 8px; text-align: center; font-weight: 600; margin-bottom: 15px; letter-spacing: 1px; text-transform: uppercase; font-size: 0.9em; background: rgba(255,255,255,0.02); }
    .kanban-todo { border-top: 3px solid #868e96; }
    .kanban-prog { border-top: 3px solid #4dabf7; }
    .kanban-review { border-top: 3px solid #fcc419; }
    .kanban-done { border-top: 3px solid #20c997; }
    
    .doc-card { background: #1a1c23; border-left: 4px solid #4dabf7; padding: 15px; border-radius: 6px; margin-bottom: 10px; transition: all 0.2s ease; }
    .doc-card:hover { background: #232630; cursor: pointer; }
    .doc-card h4 { margin: 0 0 5px 0; color: #e9ecef; }
    .doc-card p { margin: 0; color: #adb5bd; font-size: 0.85em; }
    
    /* Dialog styling overrides */
    div[data-testid="stDialog"] { border-radius: 16px; overflow: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- DB MANAGEMENT ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, role TEXT, avatar TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, title TEXT, description TEXT, status TEXT, priority TEXT, assignee_id INTEGER, creator_id INTEGER, due_date TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS docs (id INTEGER PRIMARY KEY, category TEXT, title TEXT, content TEXT, author_id INTEGER, updated_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS chat (id INTEGER PRIMARY KEY, user_id INTEGER, message TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS activity (id INTEGER PRIMARY KEY, user_id INTEGER, action TEXT, timestamp TEXT)''')
    
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO users (name, role, avatar) VALUES (?, ?, ?)", 
                      [('Alice', 'Product Manager', '👩‍💼'), ('Bob', 'Senior Developer', '👨‍💻'), ('Charlie', 'UX Designer', '🎨'), ('Diana', 'Data Scientist', '🔬')])
        c.executemany("INSERT INTO tasks (title, description, status, priority, assignee_id, creator_id, due_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      [('Revamp Landing Page UI', 'Update the hero section and add new 3D assets to the homepage.', 'In Progress', 'High', 3, 1, (datetime.date.today() + datetime.timedelta(days=2)).isoformat(), datetime.date.today().isoformat()),
                       ('Setup Auth0 Integration', 'Implement OAuth2 login for external partners.', 'To Do', 'High', 2, 1, (datetime.date.today() + datetime.timedelta(days=5)).isoformat(), datetime.date.today().isoformat()),
                       ('Analyze Q1 Churn Data', 'Identify key drop-off points in the user journey.', 'Review', 'Medium', 4, 1, datetime.date.today().isoformat(), datetime.date.today().isoformat()),
                       ('Draft Q2 Roadmap', 'Gather requirements and finalize feature list.', 'Done', 'Low', 1, 1, (datetime.date.today() - datetime.timedelta(days=3)).isoformat(), (datetime.date.today() - datetime.timedelta(days=10)).isoformat())])
        c.execute("INSERT INTO docs (category, title, content, author_id, updated_at) VALUES (?, ?, ?, ?, ?)",
                  ('Engineering', 'API Guidelines v2', '# API Guidelines\n\nAll new endpoints must follow RESTful standards.\n\n## Authentication\nUse Bearer tokens.', 2, datetime.datetime.now().isoformat()))
        c.execute("INSERT INTO activity (user_id, action, timestamp) VALUES (?, ?, ?)", (1, "initialized the workspace", datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()

def run_query(query, params=()):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute_query(query, params=()):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

def log_activity(user_id, action):
    execute_query("INSERT INTO activity (user_id, action, timestamp) VALUES (?, ?, ?)", (user_id, action, datetime.datetime.now().isoformat()))

init_db()
inject_css()

# --- CACHE DATA FOR PERFORMANCE ---
@st.cache_data(ttl=5)
def load_users():
    return run_query("SELECT * FROM users")

@st.cache_data(ttl=2)
def load_tasks():
    return run_query("SELECT * FROM tasks")

@st.cache_data(ttl=5)
def load_docs():
    return run_query("SELECT * FROM docs")

@st.cache_data(ttl=2)
def load_chat():
    return run_query("SELECT * FROM chat")

@st.cache_data(ttl=2)
def load_activity():
    return run_query("SELECT * FROM activity ORDER BY timestamp DESC LIMIT 20")

users_df = load_users()
user_dict = {row['id']: f"{row['avatar']} {row['name']}" for _, row in users_df.iterrows()}
raw_user_dict = {row['id']: row['name'] for _, row in users_df.iterrows()}

# --- SESSION STATE ---
if 'current_user_id' not in st.session_state:
    st.session_state.current_user_id = int(users_df.iloc[0]['id'])

# --- SIDEBAR & NAVIGATION ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>🌌 CollabSpace Pro</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.subheader("Profile")
    user_options = {row['id']: f"{row['avatar']} {row['name']} ({row['role']})" for _, row in users_df.iterrows()}
    selected_user_id = st.selectbox("Switch User", options=list(user_options.keys()), format_func=lambda x: user_options[x], index=list(user_options.keys()).index(st.session_state.current_user_id), label_visibility="collapsed")
    
    if selected_user_id != st.session_state.current_user_id:
        st.session_state.current_user_id = selected_user_id
        st.rerun()
        
    st.markdown("---")
    menu = st.radio("Navigation", [
        "📊 Dashboard", 
        "📋 Task Board", 
        "📅 Timeline",
        "📚 Wiki & Docs", 
        "💬 Team Chat", 
        "⚙️ Settings"
    ], label_visibility="collapsed")
    st.markdown("---")
    st.caption("v2.0 Premium Edition")

current_user_name = raw_user_dict.get(st.session_state.current_user_id, "Unknown")

# --- DIALOGS ---
@st.dialog("➕ Create New Task")
def task_dialog():
    with st.form("task_form"):
        title = st.text_input("Title", placeholder="e.g., Update Marketing Assets")
        desc = st.text_area("Description", placeholder="Add details here...")
        c1, c2 = st.columns(2)
        status = c1.selectbox("Status", ["To Do", "In Progress", "Review", "Done"])
        priority = c2.selectbox("Priority", ["Low", "Medium", "High"], index=1)
        
        c3, c4 = st.columns(2)
        assignee_name = c3.selectbox("Assignee", ["Unassigned"] + users_df['name'].tolist())
        due_date = c4.date_input("Due Date")
        
        if st.form_submit_button("Create Task", type="primary"):
            if not title:
                st.error("Title is required!")
            else:
                assignee_id = None
                if assignee_name != "Unassigned":
                    assignee_id = int(users_df[users_df['name'] == assignee_name].iloc[0]['id'])
                
                execute_query(
                    "INSERT INTO tasks (title, description, status, priority, assignee_id, creator_id, due_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (title, desc, status, priority, assignee_id, st.session_state.current_user_id, due_date.isoformat(), datetime.date.today().isoformat())
                )
                log_activity(st.session_state.current_user_id, f"created task: {title}")
                st.success("Task created!")
                time.sleep(0.5)
                load_tasks.clear()
                load_activity.clear()
                st.rerun()

@st.dialog("📝 Edit Task")
def edit_task_dialog(task):
    with st.form(f"edit_form_{task['id']}"):
        new_title = st.text_input("Title", value=task['title'])
        new_desc = st.text_area("Description", value=task['description'] if task['description'] else "")
        c1, c2 = st.columns(2)
        new_status = c1.selectbox("Status", ["To Do", "In Progress", "Review", "Done"], index=["To Do", "In Progress", "Review", "Done"].index(task['status']))
        new_priority = c2.selectbox("Priority", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(task['priority']))
        
        current_assignee = raw_user_dict.get(task['assignee_id'], "Unassigned") if pd.notna(task['assignee_id']) else "Unassigned"
        user_list = ["Unassigned"] + users_df['name'].tolist()
        new_assignee_name = st.selectbox("Assignee", user_list, index=user_list.index(current_assignee))
        
        c_date = task['due_date'] if pd.notna(task['due_date']) else datetime.date.today().isoformat()
        new_due = st.date_input("Due Date", value=datetime.date.fromisoformat(c_date) if c_date else datetime.date.today())
        
        col1, col2 = st.columns([1,1])
        submitted = col1.form_submit_button("Save Changes", type="primary")
        deleted = col2.form_submit_button("Delete Task")
        
        if submitted:
            a_id = None if new_assignee_name == "Unassigned" else int(users_df[users_df['name'] == new_assignee_name].iloc[0]['id'])
            execute_query(
                "UPDATE tasks SET title=?, description=?, status=?, priority=?, assignee_id=?, due_date=? WHERE id=?",
                (new_title, new_desc, new_status, new_priority, a_id, new_due.isoformat(), task['id'])
            )
            if new_status != task['status']:
                log_activity(st.session_state.current_user_id, f"moved task '{new_title}' to {new_status}")
            load_tasks.clear()
            load_activity.clear()
            st.rerun()
            
        if deleted:
            execute_query("DELETE FROM tasks WHERE id=?", (task['id'],))
            log_activity(st.session_state.current_user_id, f"deleted task '{new_title}'")
            load_tasks.clear()
            load_activity.clear()
            st.rerun()

# --- VIEWS ---
tasks_df = load_tasks()

if menu == "📊 Dashboard":
    st.title("Welcome back, " + current_user_name + " 👋")
    st.markdown("Here's what's happening across your projects today.")
    
    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    total_tasks = len(tasks_df)
    done_tasks = len(tasks_df[tasks_df['status'] == 'Done'])
    prog_tasks = len(tasks_df[tasks_df['status'] == 'In Progress'])
    completion_rate = int((done_tasks / total_tasks * 100)) if total_tasks > 0 else 0
    
    c1.metric("Total Tasks", total_tasks)
    c2.metric("In Progress", prog_tasks)
    c3.metric("Completed", done_tasks)
    c4.metric("Completion Rate", f"{completion_rate}%")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Analytics Charts
    colA, colB = st.columns([2, 1])
    
    with colA:
        st.subheader("📈 Task Workload Distribution")
        if total_tasks > 0:
            # Map assignee names
            chart_df = tasks_df.copy()
            chart_df['Assignee'] = chart_df['assignee_id'].apply(lambda x: raw_user_dict.get(x, 'Unassigned') if pd.notna(x) else 'Unassigned')
            
            # Count by status and assignee
            status_counts = chart_df.groupby(['Assignee', 'status']).size().reset_index(name='Count')
            
            fig = px.bar(status_counts, x="Assignee", y="Count", color="status", 
                         color_discrete_map={"To Do": "#868e96", "In Progress": "#4dabf7", "Review": "#fcc419", "Done": "#20c997"},
                         barmode="stack", template="plotly_dark")
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=20, l=0, r=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough data to display chart.")
            
    with colB:
        st.subheader("⚡ Recent Activity")
        activity_df = load_activity()
        with st.container(height=350, border=True):
            if not activity_df.empty:
                for _, row in activity_df.iterrows():
                    user_str = user_dict.get(row['user_id'], 'Unknown')
                    dt_obj = datetime.datetime.fromisoformat(row['timestamp'])
                    time_str = dt_obj.strftime("%b %d, %H:%M")
                    st.markdown(f"<div style='font-size:0.9em; margin-bottom:10px;'><b>{user_str}</b> {row['action']}<br><span style='color:#6c757d;font-size:0.8em;'>{time_str}</span></div>", unsafe_allow_html=True)
            else:
                st.write("No activity yet.")

elif menu == "📋 Task Board":
    col1, col2 = st.columns([1, 1])
    with col1:
        st.title("Task Board")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Create New Task", type="primary", use_container_width=True):
            task_dialog()
            
    # Filters
    with st.expander("🔍 Filters", expanded=False):
        fc1, fc2, fc3 = st.columns(3)
        user_list = ["All"] + users_df['name'].tolist() + ["Unassigned"]
        f_assignee = fc1.selectbox("Assignee", user_list)
        f_priority = fc2.selectbox("Priority", ["All", "High", "Medium", "Low"])
        f_search = fc3.text_input("Search Title")
    
    # Apply Filters
    filtered_df = tasks_df.copy()
    if f_assignee != "All":
        if f_assignee == "Unassigned":
            filtered_df = filtered_df[pd.isna(filtered_df['assignee_id'])]
        else:
            u_id = users_df[users_df['name'] == f_assignee].iloc[0]['id']
            filtered_df = filtered_df[filtered_df['assignee_id'] == u_id]
    if f_priority != "All":
        filtered_df = filtered_df[filtered_df['priority'] == f_priority]
    if f_search:
        filtered_df = filtered_df[filtered_df['title'].str.contains(f_search, case=False, na=False)]

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Kanban Board
    k1, k2, k3, k4 = st.columns(4)
    
    def render_kanban_card(task, target_col):
        with target_col:
            badge_class = f"badge badge-{task['priority']}"
            a_name = user_dict.get(task['assignee_id'], "👤 Unassigned") if pd.notna(task['assignee_id']) else "👤 Unassigned"
            desc_snippet = (task['description'][:60] + '...') if task['description'] and len(task['description']) > 60 else (task['description'] or "")
            
            st.markdown(f"""
            <div class="task-card">
                <div style="margin-bottom: 8px;"><span class="{badge_class}">{task['priority']}</span></div>
                <div class="task-title">{task['title']}</div>
                <div class="task-desc">{desc_snippet}</div>
                <div class="task-meta">
                    <span>{a_name}</span>
                    <span>📅 {task['due_date'] if pd.notna(task['due_date']) else 'No Date'}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Action buttons side-by-side
            bc1, bc2 = st.columns([1,1])
            if bc1.button("Edit", key=f"e_{task['id']}", use_container_width=True):
                edit_task_dialog(task)
            
            # Quick Move logic
            status_order = ["To Do", "In Progress", "Review", "Done"]
            current_idx = status_order.index(task['status'])
            next_status = status_order[current_idx + 1] if current_idx < 3 else None
            
            if next_status:
                if bc2.button(f"→ {next_status}", key=f"m_{task['id']}", use_container_width=True):
                    execute_query("UPDATE tasks SET status=? WHERE id=?", (next_status, task['id']))
                    log_activity(st.session_state.current_user_id, f"moved '{task['title']}' to {next_status}")
                    load_tasks.clear()
                    load_activity.clear()
                    st.rerun()

    with k1:
        st.markdown('<div class="kanban-header kanban-todo">To Do</div>', unsafe_allow_html=True)
        for _, task in filtered_df[filtered_df['status'] == 'To Do'].iterrows(): render_kanban_card(task, k1)
            
    with k2:
        st.markdown('<div class="kanban-header kanban-prog">In Progress</div>', unsafe_allow_html=True)
        for _, task in filtered_df[filtered_df['status'] == 'In Progress'].iterrows(): render_kanban_card(task, k2)
            
    with k3:
        st.markdown('<div class="kanban-header kanban-review">Review</div>', unsafe_allow_html=True)
        for _, task in filtered_df[filtered_df['status'] == 'Review'].iterrows(): render_kanban_card(task, k3)
            
    with k4:
        st.markdown('<div class="kanban-header kanban-done">Done</div>', unsafe_allow_html=True)
        for _, task in filtered_df[filtered_df['status'] == 'Done'].iterrows(): render_kanban_card(task, k4)

elif menu == "📅 Timeline":
    st.title("Project Timeline")
    st.markdown("Visualize tasks by due date.")
    
    if tasks_df.empty:
        st.info("No tasks available to plot.")
    else:
        # Create a Gantt chart using Plotly timeline
        timeline_df = tasks_df.copy()
        # Drop tasks without due dates or created_at for Gantt
        timeline_df = timeline_df.dropna(subset=['created_at', 'due_date'])
        
        if not timeline_df.empty:
            timeline_df['Assignee'] = timeline_df['assignee_id'].apply(lambda x: raw_user_dict.get(x, 'Unassigned') if pd.notna(x) else 'Unassigned')
            
            fig = px.timeline(timeline_df, x_start="created_at", x_end="due_date", y="Assignee", color="status",
                              hover_name="title", text="title", template="plotly_dark",
                              color_discrete_map={"To Do": "#868e96", "In Progress": "#4dabf7", "Review": "#fcc419", "Done": "#20c997"})
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=500)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Tasks must have creation and due dates to appear on the timeline.")
            
        st.subheader("Upcoming Deadlines")
        # Show table of tasks sorted by due date
        upcoming_df = tasks_df[tasks_df['status'] != 'Done'].copy()
        upcoming_df['Due Date'] = pd.to_datetime(upcoming_df['due_date']).dt.date
        upcoming_df = upcoming_df.sort_values('Due Date').head(10)
        upcoming_df['Assignee'] = upcoming_df['assignee_id'].apply(lambda x: raw_user_dict.get(x, 'Unassigned') if pd.notna(x) else 'Unassigned')
        
        display_df = upcoming_df[['title', 'status', 'priority', 'Assignee', 'Due Date']].rename(columns={'title': 'Task Title', 'status': 'Status', 'priority': 'Priority'})
        st.dataframe(display_df, use_container_width=True, hide_index=True)

elif menu == "📚 Wiki & Docs":
    st.title("Knowledge Base")
    
    docs_df = load_docs()
    
    # Dialog for new doc
    @st.dialog("Create New Document")
    def create_doc_dialog():
        title = st.text_input("Title")
        category = st.selectbox("Category", ["Engineering", "Product", "Marketing", "HR", "General"])
        if st.button("Create"):
            if title:
                execute_query("INSERT INTO docs (category, title, content, author_id, updated_at) VALUES (?, ?, ?, ?, ?)",
                              (category, title, f"# {title}\n\nStart writing...", st.session_state.current_user_id, datetime.datetime.now().isoformat()))
                log_activity(st.session_state.current_user_id, f"created document: {title}")
                load_docs.clear()
                load_activity.clear()
                st.rerun()

    c1, c2 = st.columns([1, 3])
    
    with c1:
        if st.button("➕ New Document", use_container_width=True, type="primary"):
            create_doc_dialog()
            
        st.markdown("### Categories")
        cats = ["All"] + list(docs_df['category'].unique()) if not docs_df.empty else ["All"]
        selected_cat = st.radio("Filter", cats, label_visibility="collapsed")
        
        st.markdown("### Documents")
        display_docs = docs_df if selected_cat == "All" else docs_df[docs_df['category'] == selected_cat]
        
        selected_doc_id = None
        for _, doc in display_docs.iterrows():
            if st.button(f"📄 {doc['title']}", key=f"dbtn_{doc['id']}", use_container_width=True):
                st.session_state.active_doc_id = doc['id']
                
        active_id = st.session_state.get('active_doc_id', display_docs.iloc[0]['id'] if not display_docs.empty else None)
        
    with c2:
        if active_id:
            try:
                active_doc = docs_df[docs_df['id'] == active_id].iloc[0]
                author_name = raw_user_dict.get(active_doc['author_id'], "Unknown")
                dt = datetime.datetime.fromisoformat(active_doc['updated_at']).strftime("%b %d, %Y %H:%M")
                
                header_c1, header_c2 = st.columns([4, 1])
                with header_c1:
                    st.markdown(f"<h2>{active_doc['title']}</h2>", unsafe_allow_html=True)
                    st.caption(f"📁 {active_doc['category']} | ✍️ {author_name} | 🕒 Last updated: {dt}")
                
                st.divider()
                
                t_view, t_edit = st.tabs(["👁️ View Mode", "✏️ Edit Mode"])
                with t_view:
                    with st.container(border=True):
                        st.markdown(active_doc['content'])
                with t_edit:
                    new_content = st.text_area("Content (Markdown)", value=active_doc['content'], height=400, label_visibility="collapsed")
                    ec1, ec2 = st.columns(2)
                    if ec1.button("Save Changes", type="primary"):
                        execute_query("UPDATE docs SET content=?, updated_at=? WHERE id=?", (new_content, datetime.datetime.now().isoformat(), active_id))
                        log_activity(st.session_state.current_user_id, f"updated document: {active_doc['title']}")
                        load_docs.clear()
                        load_activity.clear()
                        st.success("Saved!")
                        time.sleep(0.5)
                        st.rerun()
                    if ec2.button("Delete Document", type="secondary"):
                        execute_query("DELETE FROM docs WHERE id=?", (active_id,))
                        log_activity(st.session_state.current_user_id, f"deleted document: {active_doc['title']}")
                        st.session_state.active_doc_id = None
                        load_docs.clear()
                        load_activity.clear()
                        st.rerun()
            except IndexError:
                st.info("Document not found.")
        else:
            st.info("Select or create a document to view its contents.")

elif menu == "💬 Team Chat":
    st.title("Team Chat")
    st.markdown("Real-time collaboration and discussion.")
    
    chat_df = load_chat()
    
    # Chat container
    chat_container = st.container(height=500, border=True)
    with chat_container:
        if chat_df.empty:
            st.info("No messages yet. Start the conversation!")
        else:
            for _, msg in chat_df.iterrows():
                is_me = msg['user_id'] == st.session_state.current_user_id
                u_name = raw_user_dict.get(msg['user_id'], "Unknown")
                avatar = users_df[users_df['id'] == msg['user_id']].iloc[0]['avatar'] if not users_df[users_df['id'] == msg['user_id']].empty else '👤'
                
                with st.chat_message(name=u_name, avatar=avatar):
                    st.write(msg['message'])
                    dt = datetime.datetime.fromisoformat(msg['timestamp']).strftime("%H:%M")
                    st.caption(f"{dt}")
                    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        execute_query("INSERT INTO chat (user_id, message, timestamp) VALUES (?, ?, ?)", 
                      (st.session_state.current_user_id, prompt, datetime.datetime.now().isoformat()))
        load_chat.clear()
        st.rerun()

elif menu == "⚙️ Settings":
    st.title("Workspace Settings")
    
    st.subheader("Team Management")
    st.dataframe(users_df[['id', 'avatar', 'name', 'role']], hide_index=True, use_container_width=True)
    
    with st.expander("➕ Add New Member"):
        with st.form("add_user_form"):
            c1, c2, c3 = st.columns([1, 3, 3])
            new_avatar = c1.text_input("Avatar (Emoji)", value="👤")
            new_name = c2.text_input("Full Name")
            new_role = c3.text_input("Role Title")
            if st.form_submit_button("Add Member"):
                if new_name:
                    execute_query("INSERT INTO users (name, role, avatar) VALUES (?, ?, ?)", (new_name, new_role, new_avatar))
                    load_users.clear()
                    st.success("Member added!")
                    time.sleep(0.5)
                    st.rerun()
                    
    st.divider()
    st.subheader("Data Export")
    st.markdown("Download workspace data for backups or external analysis.")
    
    c1, c2 = st.columns(2)
    csv_tasks = tasks_df.to_csv(index=False).encode('utf-8')
    c1.download_button("📥 Download Tasks (CSV)", data=csv_tasks, file_name="tasks_export.csv", mime="text/csv", use_container_width=True)
    
    docs_export = load_docs()
    csv_docs = docs_export.to_csv(index=False).encode('utf-8')
    c2.download_button("📥 Download Docs (CSV)", data=csv_docs, file_name="docs_export.csv", mime="text/csv", use_container_width=True)
    
    st.divider()
    st.subheader("Danger Zone")
    with st.expander("Factory Reset", expanded=False):
        st.warning("This will delete all tasks, docs, chats, and activity history. This action cannot be undone.")
        if st.button("Reset All Data", type="primary"):
            execute_query("DELETE FROM tasks")
            execute_query("DELETE FROM docs")
            execute_query("DELETE FROM chat")
            execute_query("DELETE FROM activity")
            log_activity(1, "System Reset Admin Action Performed")
            st.cache_data.clear()
            st.success("Data reset successful.")
            time.sleep(1)
            st.rerun()
