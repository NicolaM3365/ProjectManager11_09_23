

from datetime import datetime

import hashlib

from flask import Flask, jsonify, render_template, request, redirect, url_for, session, json
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

from models import Project, Task # Importing the models module will create the database tables.


# A secret key is needed to use sessions - it prevents users from modifying the cookie.
app.secret_key = "Replace me with a real secret key for production use"




# with open("C:\\Users\\Nicola.Mitchell\\OneDrive - LifeScientific\\Desktop\\UCD\\3-Python\\Unit12\\ProjectManager\\data\\data/projects.json", 'r') as f:
#     data = json.load(f)

# with open("C:\\Users\\Nicola.Mitchell\\OneDrive - LifeScientific\\Desktop\\UCD\\3-Python\\Unit12\\ProjectManager\\data\\data/projects.json", 'w') as f:
#     json.dump(data, f)

   



def gravatar_url(username, size=100, default='identicon', rating='g'):
    url = 'https://secure.gravatar.com/avatar'
    hash = hashlib.md5(username.lower().encode('utf-8')).hexdigest()
    return f'{url}/{hash}?s={size}&d={default}&r={rating}'




@app.route('/')
def index():
    """Home page for the app."""
    if "username" in session:  # Check if user is logged in
        email = session["username"]
        avatar_url = gravatar_url(email)
        return render_template('index.html', avatar_url=avatar_url)
    else:
        return render_template('index.html')


@app.route("/login", methods=["GET"])
def login():
    """Login page for the app.

    If the user is not logged in, display the login form.
    """
    # If the user is already logged in, redirect back to the home page.
    if "username" in session:
        return redirect(url_for("index"))

    # Otherwise, display the login form.
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_action():
    """Login action for the app (same route as the form)."""
    # Get the username from the form field and store it in the session.
    session["username"] = request.form["username"]

    # Redirect to the home page.
    return redirect(url_for("index"))



@app.route("/logout")
def logout():
    """Logout action for the app.

    This removes the user from the session.

    Note that semantically, this should be a POST request,
    but using GET for logging out is simpler and popular.
    """
    # Get and remove the username from the session.
    # Note that the second argument is used to explicitly ignore a missing cookie,
    # rather than raising an exception.
    session.pop("username", None)

    # Redirect to the home page.
    return redirect(url_for("index"))


# @app.route('/dashboard')
# def dashboard():
#     """Dashboard page for the app."""
#     if "username" in session:  # Check if user is logged in
#         email = session["username"]
#         avatar_url = gravatar_url(email)
#         return render_template('dashboard.html', projects=data['projects'], avatar_url=avatar_url)
#     else:
#         return redirect(url_for('login'))
    

# Dashboard
@app.route('/dashboard', methods=['GET'])
def dashboard():
    try:
        with open("data/projects.json", 'r') as f:
            local_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return "Error loading project data", 500

    # Convert the loaded JSON projects data into Project objects
    project_objects = []
    for project_dict in local_data['projects']:
        tasks = project_dict.get('tasks', [])

        # Convert tasks into Task objects
        task_objects = []
        for task_dict in tasks:
            task = Task(
                task_dict['task_id'],
                task_dict['name'],
                task_dict['description'],
                task_dict['status'],
                task_dict.get('assigned_to', None)  # This accounts for if 'assigned_to' is not present
            )
            task_objects.append(task)

        # Now create the Project object
        project = Project(
            project_dict['project_id'], 
            project_dict['name'], 
            project_dict['description'], 
            task_objects
        )
        project_objects.append(project)
        
    if "username" in session:
        email = session["username"]
        avatar_url = gravatar_url(email)
        return render_template('dashboard.html', projects=project_objects, avatar_url=avatar_url)
    else:
        return redirect(url_for('login'))

# Project page
@app.route('/project/<int:project_id>', methods=['GET'])
def project_page(project_id):
    try:
        with open("data/projects.json", 'r') as f:
            local_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return "Error loading project data", 500

    project = next((item for item in local_data['projects'] if (item['project_id']) == (project_id)), None)

    
    if project is None:
        return redirect(url_for('dashboard'))

    return render_template('project_page.html', project=project)


""" create a new project with its name and description""" 
@app.route('/new_project', methods=['GET', 'POST'])
def new_project():  
    if request.method == 'POST':
        try:
            with open("data/projects.json", 'r') as f:
                local_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return "Error loading project data", 500
        
        
        # Find the largest existing project ID
        max_id = 0
        for project in local_data['projects']:
            if 'project_id' in project and project['project_id'] > max_id:
                max_id = project['project_id']

        # Generate a new unique ID
        new_project_id = max_id + 1


        new_project = {
            "project_id": new_project_id,
            "name": request.form.get('name'),
            "description": request.form.get('description')
            
        }

        local_data['projects'].append(new_project)

        with open("data/projects.json", 'w') as f:
            json.dump(local_data, f)

        return redirect(url_for('dashboard'))
    else:
        return render_template('new_project.html')




@app.route('/delete_project/<int:project_id>', methods=['POST'])
def delete_project_route(project_id):
    try:
        with open("data/projects.json", 'r') as f:
            local_data = json.load(f)

        project_to_remove = next((project for project in local_data['projects'] if project['project_id'] == project_id), None)
        
        if project_to_remove:
            local_data['projects'].remove(project_to_remove)

        with open("data/projects.json", 'w') as f:
            json.dump(local_data, f)

        return redirect(url_for('dashboard'))  # Assuming 'index' is your main page's route function

    except (FileNotFoundError, json.JSONDecodeError):
        return redirect(url_for('error_route'))  # Assuming 'error_route' is the function name for the error page








@app.route('/new_task/<int:project_id>', methods=['GET', 'POST'])
def new_task(project_id):
    if request.method == 'POST':
        try:
            with open("data/projects.json", 'r') as f:
                local_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return "Error loading project data", 500
        
        project = next((item for item in local_data['projects'] if (item['project_id']) == (project_id)), None)

        if project is None:
            return redirect(url_for('dashboard'))
        
         # Calculate the next task_id
        if project['tasks']:
            next_task_id = max(int(task['task_id']) for task in project['tasks']) + 1
        else:
            next_task_id = 1  # First task in the project

        new_task = {
            "task_id": next_task_id,
            "name": request.form.get('name'),
            "description": request.form.get('description'),
            "status": request.form.get('status')
        }

        project['tasks'].append(new_task)

        with open("data/projects.json", 'w') as f:
            json.dump(local_data, f)

        return redirect(url_for('project_page', project_id=project_id))
    else:
        return render_template('new_task.html', project_id=project_id)
        
""" deleteTask() - deletes a task from a project"""

@app.route('/delete_task/<int:project_id>/<int:task_id>', methods=['POST'])
def delete_task(project_id, task_id):
    try:
        with open("data/projects.json", 'r') as f:
            local_data = json.load(f)
    
        for project in local_data['projects']:
            if project['project_id'] == project_id:
                task_to_remove = next((item for item in project['tasks'] if item['task_id'] == task_id), None)
                if task_to_remove:
                    project['tasks'].remove(task_to_remove)
                    break

        with open("data/projects.json", 'w') as f:
            json.dump(local_data, f)

        return redirect(url_for('project_page', project_id=project_id))

    except (FileNotFoundError, json.JSONDecodeError):
        return redirect(url_for('error_route'))  # Assuming 'error_route' is the function name for the error page


@app.route('/edit_task_page/<int:project_id>/<int:task_id>', methods=['GET'])
def edit_task_page(project_id, task_id):
    try:
        # Load the existing projects and tasks from the JSON file
        with open("data/projects.json", 'r') as f:
            local_data = json.load(f)

        project_to_edit = next((project for project in local_data['projects'] if project['project_id'] == project_id), None)
        if not project_to_edit:
            return redirect(url_for('error_route'))  # Project not found

        task_to_edit = next((task for task in project_to_edit['tasks'] if task['task_id'] == task_id), None)
        if not task_to_edit:
            return redirect(url_for('error_route'))  # Task not found within the specified project

        return render_template('edit_task.html', project=project_to_edit, task=task_to_edit)

    except (FileNotFoundError, json.JSONDecodeError):
        return redirect(url_for('error_route'))  # Redirect to error page if something goes wrong




@app.route('/find_and_edit_task/<int:project_id>/<int:task_id>', methods=['POST'])
def find_and_edit_task(project_id, task_id):
    try:
        # Load the existing projects and tasks from the JSON file
        with open("data/projects.json", 'r') as f:
            local_data = json.load(f)

        # Variables to keep track of the project and task to edit
        project_to_edit = None
        task_to_edit = None

        # Locate the project using project_id
        for project in local_data['projects']:
            if project['project_id'] == project_id:
                project_to_edit = project
                break

        if not project_to_edit:
            return redirect(url_for('error_route'))  # Project not found

        # Locate the task within that project using task_id
        task_to_edit = next((task for task in project_to_edit['tasks'] if task['task_id'] == task_id), None)

        if not task_to_edit:
            return redirect(url_for('error_route'))  # Task not found within the specified project


        # Update the task data from form
        task_to_edit['name'] = request.form['name']
        task_to_edit['description'] = request.form['description']
        task_to_edit['status'] = request.form['status']
        task_to_edit['assigned_to'] = request.form['assigned_to']

        # Save updated project and tasks data back to the JSON file
        with open("data/projects.json", 'w') as f:
            json.dump(local_data, f)

        return redirect(url_for('project_page', project_id=project_id))
    

    except (FileNotFoundError, json.JSONDecodeError):
        return redirect(url_for('error_route'))  # Redirect to error page if something goes wrong



# Our very basic in-memory data store for all previous messages, reset on server restart
chat_log = []


@app.route('/chat_home')
def chat_home():
    """Render the main chat page"""
    return render_template('chat.html', messages=chat_log)


@app.route('/clear')
def clear():
    """Clear the chat log"""
    chat_log.clear()
    socketio.emit('clearChat')
    return redirect(url_for('chat_home'))


@socketio.on('chatEvent')
def handle_message(message):
    """Process a new message and broadcast it to all users"""
    chat_log.append(message)
    emit('chatEvent', message, broadcast=True)




if __name__ == '__main__':
    socketio.run(app, debug=True, port=8080)


