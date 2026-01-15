# 🤖 Pran-Bot: Autonomous IoT Environmental Guardian

**Pran-Bot** (inspired by the Sanskrit word for "Breath/Life Force") is a mobile sensing platform that bridges the gap between industrial safety and autonomous robotics. By combining a multi-gas sensing array with intelligent obstacle avoidance, it transforms static environmental monitoring into a proactive, mobile patrol system.

---

## 🧠 System Architecture & "Intelligence"

The robot operates on a multi-layer logic system:

* 
**The Sensing Layer**: A quad-sensor array (MQ-2, MQ-3, MQ-7, MQ-135) continuously samples air quality.


* 
**The Decision Engine**: If Smoke or CO levels cross critical safety thresholds (Smoke > 2000 or CO > 1500), the robot executes an "Emergency Stop".


* 
**The Mobility Layer**: Uses IR-based reactive navigation to navigate complex indoor environments autonomously.


* 
**The API Bridge**: An onboard WebServer exposes a JSON API, allowing live data visualization and Python-based AI command.



---

## 🛠 Hardware Interconnects

*Built on an ESP32 SoC for high-speed processing and dual-core performance.*

| Subsystem | Components | ESP32 Pins |
| --- | --- | --- |
| **Gas Array** | MQ-2 (Smoke), MQ-3 (CH4), MQ-7 (CO), MQ-135 (AQI) | GPIO 34, 35, 32, 33 

 |
| **Propulsion** | L298N Dual Bridge (IN1-IN4) | GPIO 25, 26, 27, 14 

 |
| **Speed Control** | Dual PWM (ENA/ENB) | GPIO 12, 13 

 |
| **Vision/Safety** | Dual Infrared (IR) Obstacle Sensors | GPIO 4, 5 

 |
| **Power** | Battery Voltage Monitoring | GPIO 36 

 |

---

## 🔬 Research & Academic Alignment

This project serves as a physical validation of the **"Indoor Air Quality Detection Robot Model"** (referenced in IEEE literature), proving that:

* **Sensor Fusion** provides a more accurate Gas Pollution Index (GPI) than single-sensor systems.
* **Autonomous Patrols** significantly reduce human exposure to hazardous leaks during initial inspection.
* **Historical Forensics** (via the PyQt dashboard) allow for data-driven compliance and safety audits.

---

## 📊 Data & Control API

The robot serves a live API for remote integration via its local Access Point **"Gas_Robot_AP"**:

* 
`GET /data`: Returns real-time sensor telemetry (Smoke, Methane, CO, Air Quality, Battery) in JSON format.


* 
`GET /cmd?d=`: Remotely overrides navigation (f=forward, b=back, l=left, r=right, s=stop).


* 
`GET /auto?v=1`: Activates the autonomous "Decision Engine".



---
