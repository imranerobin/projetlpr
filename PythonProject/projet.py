import sys
import ssl
import paho.mqtt.client as mqtt
import json
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from datetime import datetime

# Configuration HiveMQ Cloud
BROKER = "47567f9a74b445e6bef394abec5c83a1.s1.eu.hivemq.cloud"
PORT = 8883  # Port MQTT sécurisé (NON WebSocket)
TOPIC = "shellyplusplugs-e465b8b41e28/#"
USERNAME = "ShellyPlusPlugS"
PASSWORD = "Ciel92110"

class ShellyMQTTApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Infos Shelly ")
        self.setGeometry(100, 100, 400, 300)

        # Interface utilisateur
        self.layout = QVBoxLayout()

        self.status_label = QLabel("Connexion en cours...")
        self.layout.addWidget(self.status_label)

        self.power_label = QLabel("Puissance : -")
        self.layout.addWidget(self.power_label)

        self.voltage_label = QLabel("Tension : -")
        self.layout.addWidget(self.voltage_label)

        self.timestamp_label = QLabel("Date réception : -")
        self.layout.addWidget(self.timestamp_label)

        self.reconnect_button = QPushButton("Reconnexion MQTT")
        self.reconnect_button.clicked.connect(self.reconnect_mqtt)
        self.layout.addWidget(self.reconnect_button)

        self.setLayout(self.layout)

        # Initialisation MQTT
        self.client = mqtt.Client(protocol=mqtt.MQTTv5)
        self.client.username_pw_set(USERNAME, PASSWORD)
        self.client.tls_set(cert_reqs=ssl.CERT_NONE)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_log = self.on_log

        # Démarrer la connexion MQTT
        self.init_mqtt()

    def init_mqtt(self):
        try:
            print("Tentative de connexion au broker MQTT...")
            self.client.connect(BROKER, PORT, 60)
            self.client.loop_start()
        except Exception as e:
            self.status_label.setText(f"Erreur de connexion MQTT : {e}")
            print(f"Erreur de connexion : {e}")

    def on_connect(self, client, userdata, flags, rc, properties=None):
        print(f"Code de connexion MQTT : {rc}")
        if rc == 0:
            self.status_label.setText("✅ Connecté au broker MQTT")
            print("Abonnement au topic...")
            client.subscribe(TOPIC)
        else:
            self.status_label.setText(f"❌ Échec de la connexion MQTT : Code {rc}")

    def on_message(self, client, userdata, msg):
        print(f"Message reçu sur le topic {msg.topic}: {msg.payload.decode('utf-8')}")
        try:
            payload = msg.payload.decode("utf-8")
            data = json.loads(payload)

            if isinstance(data, dict) and "params" in data and "switch:0" in data["params"]:
                switch_data = data["params"]["switch:0"]
                power = switch_data.get("apower", "N/A")
                voltage = switch_data.get("current", "N/A")
                timestamp = switch_data.get("ts", 0)

                self.power_label.setText(f"Puissance : {power} W")
                self.voltage_label.setText(f"Tension : {voltage} V")

                if isinstance(timestamp, (int, float)) and timestamp > 0:
                    dt = datetime.utcfromtimestamp(timestamp)
                    self.timestamp_label.setText(f"Date réception : {dt.strftime('%d %b %Y %H:%M:%S')}")
        except json.JSONDecodeError:
            print("Erreur : Impossible de décoder le JSON.")
        except KeyError as e:
            print(f"Erreur : Clé manquante dans le message ({e}).")
        except Exception as e:
            print(f"Erreur inattendue : {e}")

    def on_log(self, client, userdata, level, buf):
        print(f"Log MQTT : {buf}")

    def reconnect_mqtt(self):
        self.client.loop_stop()
        self.init_mqtt()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ShellyMQTTApp()
    window.show()
    sys.exit(app.exec())

