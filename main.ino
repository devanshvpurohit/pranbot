#include "arduino_secrets.h"

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>

// ================= WIFI =================
const char* ssid = "Gas_Robot_AP";
const char* password = "12345678";

// ================= SERVER =================
WebServer server(80);

// ================= MQ SENSOR PINS =================
#define MQ2_PIN     34   // Smoke / Combustion
#define MQ3_PIN     35   // Methane
#define MQ7_PIN     32   // CO
#define MQ135_PIN   33   // Air Quality
#define BAT_PIN     36   // Battery

// ================= IR SENSORS =================
#define IR_LEFT_PIN   4
#define IR_RIGHT_PIN  5

// ================= L298N MOTOR =================
#define IN1 25
#define IN2 26
#define IN3 27
#define IN4 14
#define ENA 12
#define ENB 13

// ================= AUTONOMOUS =================
bool autonomous = false;
unsigned long lastAutoMove = 0;

// ================= MOTOR CONTROL =================
void stopRobot() {
  digitalWrite(IN1, LOW); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW); digitalWrite(IN4, LOW);
  ledcWrite(0, 0);
  ledcWrite(1, 0);
}

void moveRobot(String dir, int speed) {
  ledcWrite(0, speed);
  ledcWrite(1, speed);

  if (dir == "f") {
    digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
    digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
  } else if (dir == "b") {
    digitalWrite(IN1, LOW); digitalWrite(IN2, HIGH);
    digitalWrite(IN3, LOW); digitalWrite(IN4, HIGH);
  } else if (dir == "l") {
    digitalWrite(IN1, LOW); digitalWrite(IN2, HIGH);
    digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
  } else if (dir == "r") {
    digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
    digitalWrite(IN3, LOW); digitalWrite(IN4, HIGH);
  } else {
    stopRobot();
  }
}

// ================= AUTONOMOUS LOGIC =================
void autonomousLogic() {
  int irL = digitalRead(IR_LEFT_PIN);
  int irR = digitalRead(IR_RIGHT_PIN);

  int smoke = analogRead(MQ2_PIN);
  int co    = analogRead(MQ7_PIN);

  // ð´ GAS DANGER â STOP IMMEDIATELY
  if (smoke > 2000 || co > 1500) {
    stopRobot();
    return;
  }

  // ð¤ OBSTACLE AVOIDANCE
  if (irL == LOW && irR == LOW) {
    moveRobot("b", 180);
    delay(300);
    moveRobot("l", 180);
    delay(300);
  }
  else if (irL == LOW) {
    moveRobot("r", 180);
  }
  else if (irR == LOW) {
    moveRobot("l", 180);
  }
  else {
    moveRobot("f", 200);
  }
}

// ================= SETUP =================
void setup() {
  Serial.begin(115200);

  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT);

  pinMode(IR_LEFT_PIN, INPUT);
  pinMode(IR_RIGHT_PIN, INPUT);

  ledcSetup(0, 1000, 8);
  ledcAttachPin(ENA, 0);

  ledcSetup(1, 1000, 8);
  ledcAttachPin(ENB, 1);

  WiFi.softAP(ssid, password);
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.softAPIP());

  // ================= API =================
  server.on("/data", HTTP_GET, []() {
    String json = "{";
    json += "\"smoke\":" + String(analogRead(MQ2_PIN)) + ",";
    json += "\"methane\":" + String(analogRead(MQ3_PIN)) + ",";
    json += "\"co\":" + String(analogRead(MQ7_PIN)) + ",";
    json += "\"air\":" + String(analogRead(MQ135_PIN)) + ",";
    json += "\"battery\":" + String(analogRead(BAT_PIN)) + ",";
    json += "\"ir_left\":" + String(digitalRead(IR_LEFT_PIN)) + ",";
    json += "\"ir_right\":" + String(digitalRead(IR_RIGHT_PIN));
    json += "}";
    server.send(200, "application/json", json);
  });

  server.on("/cmd", HTTP_GET, []() {
    if (autonomous) {
      server.send(403, "text/plain", "AUTONOMOUS ACTIVE");
      return;
    }
    String d = server.arg("d");
    if (d == "s") stopRobot();
    else moveRobot(d, 200);
    server.send(200, "text/plain", "OK");
  });

  server.on("/auto", HTTP_GET, []() {
    String v = server.arg("v");
    autonomous = (v == "1");
    if (!autonomous) stopRobot();
    server.send(200, "text/plain", autonomous ? "AUTO ON" : "AUTO OFF");
  });

  server.begin();
}

// ================= LOOP =================
void loop() {
  server.handleClient();

  if (autonomous && millis() - lastAutoMove > 150) {
    autonomousLogic();
    lastAutoMove = millis();
  }
}
//qwerty
