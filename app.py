from flask import Flask, render_template,jsonify, request, redirect, session, url_for
import serial
import time
from datetime import datetime
import json
import multiprocessing



app = Flask(__name__)
app.secret_key = "342150"  # Secure your application with a secret key

# Set up serial communication with Arduino (Adjust COM port for your system)
try:
    ser = serial.Serial('COM6', 9600)  # Adjust the COM port based on your system
    time.sleep(2)  # Give time for the connection to establish
except serial.SerialException:
    ser = None
    print("Error: Unable to connect to Arduino")

# Track the previous state of the light to prevent it from being overwritten
previous_light_state = None

with open("users.json", "r") as f:
    users = json.load(f)["users"]
def load_users():
    with open("users.json", "r") as file:
        return json.load(file)
# Chat and usage history storage
CHAT_DATA_FILE = "chat_data.json"
USAGE_HISTORY_FILE = "usage_history.json"  # File to store usage logs

# Helper to load chat data
def load_chat_data():
    try:
        with open(CHAT_DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# Helper to save chat data
def save_chat_data(data):
    with open(CHAT_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


# Helper to log usage
def log_usage(action, device):
    try:
        with open(USAGE_HISTORY_FILE, "r") as f:
            usage_data = json.load(f)
    except FileNotFoundError:
        usage_data = []

    usage_data.append({
        "device": device,
        "action": action,
        "timestamp": datetime.now().isoformat(),
        "user": session.get("email")  # Capture the current logged-in user
    })

    with open(USAGE_HISTORY_FILE, "w") as f:
        json.dump(usage_data, f, indent=4)


@app.route("/chat", methods=["GET", "POST"])
def chat():
    if "email" not in session:
        return redirect(url_for("login"))

    email = session["email"]
    chat_data = load_chat_data()  # Load chat data from a file or database
    user_role = users[email]["role"]

    if request.method == "POST":
        # Handle new message via AJAX
        message = request.form.get("message")
        recipient = request.form.get("recipient")
        
        if not recipient or not message:
            return jsonify({"error": "Recipient and message are required"}), 400

        # Ensure chat_data structure exists for both sender and recipient
        if email not in chat_data:
            chat_data[email] = {}
        if recipient not in chat_data[email]:
            chat_data[email][recipient] = []

        # Append the message to the sender's chat history
        chat_data[email][recipient].append({"message": message, "sent": True, "timestamp": datetime.now().isoformat()})

        # Ensure recipient also has the sender's message
        if recipient not in chat_data:
            chat_data[recipient] = {}
        if email not in chat_data[recipient]:
            chat_data[recipient][email] = []

        # Append the message to the recipient's chat history
        chat_data[recipient][email].append({"message": message, "sent": False, "timestamp": datetime.now().isoformat()})

        # Save the updated chat data (this could be a file or database)
        save_chat_data(chat_data)

        # Respond with the new message and timestamp to update the UI
        return jsonify({
            "message": message,
            "sent": True,
            "timestamp": datetime.now().isoformat()
        })

    # List of users to select from (excluding the current logged-in user)
    users_list = {email: user["name"] for email, user in users.items() if email != session["email"]}

    # Get the recipient from query parameters (for showing chat history with a specific user)
    recipient = request.args.get("recipient")
    
    # Retrieve chat history with the selected recipient (if any)
    chat_history = chat_data.get(email, {}).get(recipient, [])

    # Render the chat template with the users list, recipient, and chat history
    return render_template("chat.html", users_list=users_list, recipient=recipient, chat_history=chat_history, user_role=user_role)


@app.route("/get_messages", methods=["GET"])
def get_messages():
    if "email" not in session:
        return redirect(url_for("login"))
    
    email = session["email"]
    recipient = request.args.get("recipient")
    
    if not recipient:
        return jsonify({"error": "Recipient required"}), 400
    
    chat_data = load_chat_data()
    chat_history = chat_data.get(email, {}).get(recipient, [])
    
    return jsonify({"chat_history": chat_history})



@app.route('/')
def home():
    # Redirect to login if not authenticated
    if "email" not in session:
        return redirect(url_for("login"))
    user = users[session["email"]]
    if user["role"] == "admin":
        return render_template("admin_dashboard.html", username=user["name"])
    elif user["role"] == "student":
        return render_template("student_dashboard.html", student_name=user["name"])
    return "Unauthorized", 403

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if email in users and users[email]["password"] == password:
            session["email"] = email
            return redirect(url_for("home"))
        return render_template("login.html", error="Invalid credentials!")
    return render_template("login.html")

@app.route('/control_fan', methods=['POST'])
def control_fan():
    if ser is None:
        log_usage("Arduino not connected - Fan control failed", "Fan")
        return "Arduino not connected"
    
    # Get the fan slider value from the AJAX request
    fan_speed = int(request.form.get('fan_slider'))

    # Control the fan based on slider value
    if fan_speed == 0:
        ser.write(b'FAN_OFF\n') 
        log_usage("Fan turned off", "Fan") # Send FAN OFF signal to Arduino
    elif fan_speed == 50:
        ser.write(b'FAN_50\n') 
        log_usage("Fan set to 50% speed", "Fan") # Send FAN 50% speed signal to Arduino
    elif fan_speed == 100:
        ser.write(b'FAN_100\n') 
        log_usage("Fan set to 100% speed", "Fan") # Send FAN 100% speed signal to Arduino

    return 'Fan control command sent!'

@app.route('/control_light', methods=['POST'])
def control_light():
    global previous_light_state

    if ser is None:
        log_usage("Arduino not connected - Light control failed", "Light")
        return "Arduino not connected"
    
    # Get the light state from the AJAX request
    light_state = request.form.get('light_state')

    # Only send the light command if the light state has changed
    if light_state != previous_light_state:
        if light_state == 'on':
            ser.write(b'LIGHT_ON\n') 
            log_usage("Light turned on", "Light") # Turn light ON
        else:
            ser.write(b'LIGHT_OFF\n') 
            log_usage("Light turned off", "Light") # Turn light OFF

        # Update the previous state
        previous_light_state = light_state

    return f'Light turned {light_state}!'

@app.route('/usage_history')
def usage_history():
    if "email" not in session:
        return redirect(url_for("login"))

    try:
        with open(USAGE_HISTORY_FILE, "r") as f:
            usage_data = json.load(f)
    except FileNotFoundError:
        usage_data = []

    return render_template("usage_history.html", usage_data=usage_data)

@app.route('/usage_history/api', methods=['GET'])
def usage_history_api():
    if "email" not in session:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        with open(USAGE_HISTORY_FILE, "r") as f:
            usage_data = json.load(f)
    except FileNotFoundError:
        usage_data = []

    return jsonify(usage_data)


@app.route('/admin/register', methods=["GET", "POST"])
def register_user():
    if "email" not in session or users[session["email"]]["role"] != "admin":
        return "Unauthorized", 403

    if request.method == "POST":
        new_email = request.form.get("email")
        new_password = request.form.get("password")
        new_name = request.form.get("name")
        new_role = request.form.get("role")

        if not new_email or not new_password or not new_name or new_role not in ["admin", "student"]:
            return render_template("register_user.html", error="Invalid input!")

        if new_email in users:
            return render_template("register_user.html", error="User already exists!")

        # Add the new user
        users[new_email] = {
            "name": new_name,
            "password": new_password,
            "role": new_role
        }
        with open("users.json", "w") as f:
            json.dump({"users": users}, f, indent=4)

        return redirect(url_for("manage_users"))

    return render_template("register_user.html")

@app.route('/admin/manage', methods=["GET", "POST"])
def manage_users():
    if "email" not in session or users[session["email"]]["role"] != "admin":
        return "Unauthorized", 403

    if request.method == "POST":
        action = request.form.get("action")
        target_email = request.form.get("email")

        if action == "delete" and target_email in users:
            del users[target_email]
            with open("users.json", "w") as f:
                json.dump({"users": users}, f, indent=4)

    return render_template("manage_users.html", users=users)


@app.route('/logout')
def logout():
    session.pop("email", None)
    return redirect(url_for("login"))

if __name__ == '__main__':
    app.run(host='192.168.4.2', port=5000, ssl_context=('cert.pem', 'key.pem'), threaded=True)
