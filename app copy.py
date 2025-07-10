from flask import Flask, render_template, request
import serial
import time

app = Flask(__name__)

# Set up serial communication with Arduino (Adjust COM port for your system)
try:
    ser = serial.Serial('COM6', 9600)  # Adjust the COM port based on your system
    time.sleep(2)  # Give time for the connection to establish
except serial.SerialException:
    ser = None
    print("Error: Unable to connect to Arduino")

# Track the previous state of the light to prevent it from being overwritten
previous_light_state = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/control_fan', methods=['POST'])
def control_fan():
    if ser is None:
        return "Arduino not connected"
    
    # Get the fan slider value from the AJAX request
    fan_speed = int(request.form.get('fan_slider'))

    # Control the fan based on slider value
    if fan_speed == 0:
        ser.write(b'FAN_OFF\n')  # Send FAN OFF signal to Arduino
    elif fan_speed == 50:
        ser.write(b'FAN_50\n')  # Send FAN 50% speed signal to Arduino
    elif fan_speed == 100:
        ser.write(b'FAN_100\n')  # Send FAN 100% speed signal to Arduino

    return 'Fan control command sent!'

@app.route('/control_light', methods=['POST'])
def control_light():
    global previous_light_state

    if ser is None:
        return "Arduino not connected"
    
    # Get the light state from the AJAX request
    light_state = request.form.get('light_state')

    # Only send the light command if the light state has changed
    if light_state != previous_light_state:
        if light_state == 'on':
            ser.write(b'LIGHT_ON\n')  # Turn light ON
        else:
            ser.write(b'LIGHT_OFF\n')  # Turn light OFF

        # Update the previous state
        previous_light_state = light_state

    return f'Light turned {light_state}!'

if __name__ == '__main__':
    app.run(host='192.168.4.3', port=5000)  # Use your specified IP address and port
