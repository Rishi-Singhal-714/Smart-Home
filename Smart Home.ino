
#include <WiFi.h>
#include <WiFiClient.h>
#include <WebServer.h>
#include <uri/UriBraces.h>

#define WIFI_SSID "Galaxy M31s"
#define WIFI_PASSWORD "lohia123"
#define WIFI_CHANNEL 6

WebServer server(80);

#define FAN_ON_OFF_RELAY_PIN 12
#define FAN_SPEED_RELAY_PIN 13
#define LIGHT_RELAY_PIN 4
#define NEW_RELAY_PIN 14
int fanSpeedCounter = 0;

void setupRelays() {
  pinMode(FAN_ON_OFF_RELAY_PIN, OUTPUT);
  pinMode(FAN_SPEED_RELAY_PIN, OUTPUT);
  pinMode(LIGHT_RELAY_PIN, OUTPUT);
  pinMode(NEW_RELAY_PIN, OUTPUT);

  digitalWrite(FAN_ON_OFF_RELAY_PIN, HIGH);
  digitalWrite(FAN_SPEED_RELAY_PIN, HIGH);
  digitalWrite(LIGHT_RELAY_PIN, HIGH);
  digitalWrite(NEW_RELAY_PIN, HIGH);
}

void sendHtml() {
  String response = R"(
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Smart Home Control</title>
      <style>
        body {
          font-family: Arial, sans-serif;
          background: linear-gradient(-60deg, #6c3 50%, #09f 50%);
          text-align: center;
        }

        .content {
          background-color: rgba(245, 232, 232, 0.473);
          border-radius: 0.25em;
          box-shadow: 0 0 0.25em rgba(0, 0, 0, 0.975);
          box-sizing: border-box;
          left: 50%;
          padding: 10vmin;
          position: fixed;
          text-align: center;
          top: 50%;
          transform: translate(-50%, -50%);
        }

        h1 {
          font-family: Cambria, Cochin, Georgia, Times, 'Times New Roman', serif;
        }

        .range {
          margin-top: 20px;
          height: 25px;
          align-items: center;
          width: 350px;
          background: #fff;
          border-radius: 10px;
          padding: 0 65px 0 45px;
          box-shadow: 2px 4px 8px rgba(0, 0, 0, 0.1);
        }

        .sliderValue {
          position: relative;
          width: 100%;
        }

        .sliderValue span {
          position: absolute;
          height: 45px;
          width: 45px;
          transform: translateX(-70%) scale(0);
          font-weight: 500;
          top: -40px;
          line-height: 55px;
          z-index: 2;
          color: #fff;
          transform-origin: bottom;
          transition: transform 0.3s ease-in-out;
        }

        .sliderValue span.show {
          transform: translateX(-70%) scale(1);
        }

        .sliderValue span:after {
          position: absolute;
          content: '';
          height: 100%;
          width: 100%;
          background: #664AFF;
          border: 3px solid #fff;
          z-index: -1;
          left: 50%;
          transform: translateX(-50%) rotate(45deg);
          border-bottom-left-radius: 50%;
          box-shadow: 0px 0px 8px rgba(0, 0, 0, 0.1);
          border-top-left-radius: 50%;
          border-top-right-radius: 50%;
        }

        .field {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100%;
          position: relative;
        }

        .field .value {
          position: absolute;
          font-size: 18px;
          color: #664AFF;
          font-weight: 600;
        }

        .field .value.left {
          left: -22px;
        }

        .field .value.right {
          right: -43px;
        }

        .range input {
          width: 100%;
          height: 3px;
          background: #ddd;
          border-radius: 5px;
          outline: none;
          border: none;
          z-index: 2222;
        }

        .range input::-webkit-slider-thumb {
          -webkit-appearance: none;
          width: 20px;
          height: 20px;
          background: red;
          border-radius: 50%;
          background: #664AFF;
          border: 1px solid #664AFF;
          cursor: pointer;
        }

        .range input::-moz-range-thumb {
          width: 20px;
          height: 20px;
          background: red;
          border-radius: 50%;
          background

: #664AFF;
          border: 1px solid #664AFF;
          cursor: pointer;
        }

        .range input::-moz-range-progress {
          background: #664AFF;
        }
      </style>
    </head>
    <body>

      <div class="content">
        <h1>Smart Home Control</h1>

        <div class="bg">
          <div class="control">
            <button id="lightOffButton">Turn Off Light</button>
            <button id="lightOnButton">Turn On Light</button>
          </div>
        </div>
        <br>

        <div class="bg bg2">
          <div class="control">
            <label id="fanSpeedLabel">Fan Speed:</label>
            <div class="range">
              <div class="sliderValue">
                <div class="field">
                  <div class="value left">0</div>
                  <input type="range" min="0" max="4" value="0" step="1" id="fanSpeed">
                  <div class="value right">0</div>
                </div>
              </div>
            </div>
            <button id="setFanSpeedButton">Set Fan Speed</button>
          </div>
        </div>

        <div class="bg bg3">
          <div>
            <h2>Current Temperature: <input id="currentTemperature" disabled>--</input> °C</h2>
          </div>
        </div>
      </div>
      <script>
        document.addEventListener('DOMContentLoaded', function() {
          document.getElementById('lightOffButton').addEventListener('click', function() {
            controlLight(true);
          });

          document.getElementById('lightOnButton').addEventListener('click', function() {
            controlLight(false);
          });

          document.getElementById('setFanSpeedButton').addEventListener('click', function() {
            var fanSpeed = document.getElementById('fanSpeed').value;
            setFanSpeed(fanSpeed);
          });

          function controlLight(on) {
            var url = on ? '/control?light=on' : '/control?light=off';
            fetch(url, { method: 'POST' })
              .then(response => {
                if (!response.ok) {
                  throw new Error('Network response was not ok');
                }
                return response.text();
              })
              .then(data => {
                console.log('Response:', data);
              })
              .catch(error => {
                console.error('There was a problem with the fetch operation:', error);
              });
          }

          function setFanSpeed(speed) {
            var url = '/control?fanSpeed=' + speed;
            fetch(url, { method: 'POST' })
              .then(response => {
                if (!response.ok) {
                  throw new Error('Network response was not ok');
                }
                return response.text();
              })
              .then(data => {
                console.log('Response:', data);
              })
              .catch(error => {
                console.error('There was a problem with the fetch operation:', error);
              });
          }

          const slideValue = document.querySelector(".value.right");
          const inputSlider = document.querySelector("input");
          inputSlider.oninput = (() => {
            let value = inputSlider.value;
            slideValue.textContent = value;
            slideValue.classList.add("show");
          });
          inputSlider.onblur = (() => {
            slideValue.classList.remove("show");
          });
        });
      </script>
    </body>
    </html>
  )";

  server.send(200, "text/html", response);
}

void setup(void) {
  Serial.begin(115200);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD, WIFI_CHANNEL);
  Serial.print("Connecting to WiFi ");
  Serial.print(WIFI_SSID);

  while (WiFi.status() != WL_CONNECTED) {
    delay(100);
    Serial.print(".");
  }
  Serial.println(" Connected!");

  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  setupRelays();

  server.on("/", sendHtml);
  server.on("/control", HTTP_POST, []() {
    String lightStatus = server.arg("light");
    String fanSpeed = server.arg("fanSpeed");

    if (lightStatus == "on") {
      digitalWrite(LIGHT_RELAY_PIN, LOW);
    } else if (lightStatus == "off") {
      digitalWrite(LIGHT_RELAY_PIN, HIGH);
    }

    if (fanSpeed == "1") {
      digitalWrite(FAN_SPEED_RELAY_PIN, HIGH);
      fanSpeedCounter = 0;
    } else if (fanSpeed == "2") {
      digitalWrite(FAN_SPEED_RELAY_PIN, LOW);
      fanSpeedCounter = 0;
      
    }else if (fanSpeed == "3") {
      digitalWrite(NEW_RELAY_PIN, HIGH);
    } else if (fanSpeed == "4") {
      digitalWrite(NEW_RELAY_PIN, LOW);
    } 
    else if (fanSpeed == "0") {
      fanSpeedCounter++;

      if (fanSpeedCounter % 2 == 1) {
        digitalWrite(FAN_ON_OFF_RELAY_PIN, LOW);
      } else {
        digitalWrite(FAN_ON_OFF_RELAY_PIN, HIGH);
      }
    }


    server.send(200, "text/plain", "Control request received");
  });

  server.begin();
  Serial.println("HTTP server started");
}

void loop(void) {
  server.handleClient();
}
