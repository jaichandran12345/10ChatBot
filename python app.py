from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # For sessions

# Load the Q&A dataset and users data
DATASET_FILE = os.path.join(os.path.dirname(__file__), "questions.json")
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

try:
    with open(DATASET_FILE, "r") as file:
        qa_data = json.load(file)
except FileNotFoundError:
    qa_data = []

try:
    with open(USERS_FILE, "r") as file:
        users_data = json.load(file)
except FileNotFoundError:
    users_data = []

@app.route('/')
def home():
    if 'user' in session:
        return render_template_string(HTML_TEMPLATE, logged_in=True)
    return render_template_string(HTML_TEMPLATE, logged_in=False)

@app.route('/api/get_answer', methods=['POST'])
def get_answer():
    data = request.json
    user_input = data.get("query", "").lower()
    subject = data.get("subject", "").lower()

    answers = [
        entry for entry in qa_data
        if subject in entry['subject'].lower() and user_input in entry['question'].lower()
    ]
    if answers:
        return jsonify({"answer": answers[0]['answer']})
    else:
        return jsonify({"answer": "Sorry, I could not find an answer to your question."})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = next((u for u in users_data if u['username'] == username), None)
        if user and check_password_hash(user['password'], password):
            session['user'] = username
            return redirect(url_for('home'))
        return "Invalid credentials, please try again."
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        users_data.append({"username": username, "password": hashed_password})

        with open(USERS_FILE, "w") as file:
            json.dump(users_data, file)

        return redirect(url_for('login'))
    return render_template_string(SIGNUP_TEMPLATE)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        subject = request.form['subject']
        question = request.form['question']
        answer = request.form['answer']

        new_question = {"subject": subject, "question": question, "answer": answer}

        qa_data.append(new_question)

        with open(DATASET_FILE, "w") as file:
            json.dump(qa_data, file)

        return redirect(url_for('home'))

    return render_template_string(ADD_QUESTION_TEMPLATE)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Class 10 Chatbot</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background-color: black;
            color: white;
        }
        .container {
            width: 400px;
            background: #333;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
            padding: 20px;
            border-radius: 5px;
        }
        h1 {
            text-align: center;
            color: #fff;
        }
        .chatbox {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        #chat {
            height: 300px;
            overflow-y: auto;
            border: 1px solid #444;
            padding: 10px;
            border-radius: 5px;
            background: #222;
        }
        .user-query {
            text-align: right;
            color: #0099cc;
        }
        .bot-response {
            text-align: left;
            color: #fff;
        }
        input, select, button {
            padding: 10px;
            margin-top: 10px;
            border: 1px solid #444;
            border-radius: 5px;
            background-color: #555;
            color: white;
        }
        button {
            background: #0099cc;
            cursor: pointer;
        }
        button:hover {
            background: #0077aa;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Class 10 Chatbot</h1>
        
        {% if logged_in %}
            <p>Welcome, {{ session['user'] }}! <a href="/logout">Logout</a></p>
            <a href="/add_question" style="color: #0099cc;">Add New Question</a>
        {% else %}
            <a href="/login" style="color: #0099cc;">Login</a> | <a href="/signup" style="color: #0099cc;">Signup</a>
        {% endif %}

        <div class="chatbox">
            <div id="chat"></div>
            <input type="text" id="query" placeholder="Ask your question" style="background: #444; border: 1px solid #666; color: white;">
            <select id="subject">
                <option value="math">Math</option>
                <option value="science">Science</option>
                <option value="social">Social Science</option>
            </select>
            <button id="send">Ask</button>
        </div>
    </div>
    <script>
        document.getElementById("send").addEventListener("click", async () => {
            const query = document.getElementById("query").value.trim();
            const subject = document.getElementById("subject").value;

            const chat = document.getElementById("chat");
            if (!query) {
                chat.innerHTML += `<div class='bot-response'>Please enter a question.</div>`;
                return;
            }

            chat.innerHTML += `<div class='user-query'>${query}</div>`;

            try {
                const response = await fetch("/api/get_answer", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ query, subject }),
                });
                const data = await response.json();
                chat.innerHTML += `<div class='bot-response'>${data.answer}</div>`;
            } catch (err) {
                chat.innerHTML += `<div class='bot-response'>Error fetching the response. Please try again.</div>`;
            }

            document.getElementById("query").value = "";
        });
    </script>
</body>
</html>
'''

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background-color: black;
            color: white;
        }
        .container {
            width: 300px;
            background: #333;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
        }
        input, button {
            width: 100%;
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            border: 1px solid #444;
            background-color: #555;
            color: white;
        }
        button {
            background-color: #0099cc;
            cursor: pointer;
        }
        button:hover {
            background-color: #0077aa;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Login</h1>
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <p>Don't have an account? <a href="/signup" style="color: #0099cc;">Sign Up</a></p>
    </div>
</body>
</html>
'''

SIGNUP_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Signup</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background-color: black;
            color: white;
        }
        .container {
            width: 300px;
            background: #333;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
        }
        input, button {
            width: 100%;
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            border: 1px solid #444;
            background-color: #555;
            color: white;
        }
        button {
            background-color: #0099cc;
            cursor: pointer;
        }
        button:hover {
            background-color: #0077aa;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Sign Up</h1>
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Sign Up</button>
        </form>
        <p>Already have an account? <a href="/login" style="color: #0099cc;">Login</a></p>
    </div>
</body>
</html>
'''

ADD_QUESTION_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Add Question</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background-color: black;
            color: white;
        }
        .container {
            width: 400px;
            background: #333;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
        }
        input, textarea, select, button {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            border: 1px solid #444;
            background-color: #555;
            color: white;
        }
        button {
            background-color: #0099cc;
            cursor: pointer;
        }
        button:hover {
            background-color: #0077aa;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Add New Question</h1>
        <form method="POST">
            <select name="subject" required>
                <option value="math">Math</option>
                <option value="science">Science</option>
                <option value="social">Social Science</option>
            </select>
            <textarea name="question" placeholder="Question" required></textarea>
            <textarea name="answer" placeholder="Answer" required></textarea>
            <button type="submit">Submit</button>
        </form>
    </div>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)
