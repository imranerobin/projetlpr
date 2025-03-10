import sys
import ssl
import json
import paho.mqtt.client as mqtt
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QScrollArea, QFrame
)
import requests

# Configuration MQTT
BROKER = "47567f9a74b445e6bef394abec5c83a1.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "ShellyPlusPlugS"
PASSWORD = "Ciel92110"

def send_http_request(ip, turn_on):
    url = f"http://{ip}/relay/0?turn={'on' if turn_on else 'off'}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        print(f"✅ Requête envoyée avec succès : {url}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de l'envoi de la requête : {e}")

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard")
        self.setGeometry(100, 100, 500, 400)

        self.layout = QVBoxLayout()

        self.add_button = QPushButton("➕ Ajouter une prise Shelly")
        self.add_button.clicked.connect(self.ouvrir_formulaire)
        self.layout.addWidget(self.add_button)

        self.prises_layout = QVBoxLayout()
        self.scroll_area = QScrollArea()
        self.scroll_content = QWidget()
        self.scroll_content.setLayout(self.prises_layout)

        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_content)

        self.layout.addWidget(self.scroll_area)

        self.setLayout(self.layout)

    def ouvrir_formulaire(self):
        self.form_window = FormulaireWindow(self)
        self.form_window.show()

    def ajouter_prise(self, name, topic, ip):
        nouvelle_prise = ShellyWidget(name, topic, ip)
        self.prises_layout.addWidget(nouvelle_prise)

class FormulaireWindow(QWidget):
    def __init__(self, dashboard):
        super().__init__()
        self.dashboard = dashboard
        self.setWindowTitle("Formulaire - Ajouter Prise Shelly")
        self.setGeometry(150, 150, 400, 200)

        layout = QVBoxLayout()

        self.name_label = QLabel("Nom de la prise Shelly :")
        self.name_input = QLineEdit()

        self.topic_label = QLabel("Topic MQTT :")
        self.topic_input = QLineEdit()

        self.ip_label = QLabel("Adresse IP :")
        self.ip_input = QLineEdit()

        self.create_button = QPushButton("Créer")
        self.create_button.clicked.connect(self.creer_prise_shelly)

        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)
        layout.addWidget(self.topic_label)
        layout.addWidget(self.topic_input)
        layout.addWidget(self.ip_label)
        layout.addWidget(self.ip_input)
        layout.addWidget(self.create_button)

        self.setLayout(layout)

    def creer_prise_shelly(self):
        name = self.name_input.text()
        topic = self.topic_input.text()
        ip = self.ip_input.text()

        if name and topic and ip:
            self.dashboard.ajouter_prise(name, topic, ip)
            self.close()
        else:
            print("❌ Veuillez remplir tous les champs.")

class ShellyWidget(QFrame):
    def __init__(self, name, topic, ip):
        super().__init__()
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(2)

        self.name = name
        self.topic = topic
        self.ip = ip

        self.layout = QVBoxLayout()

        self.name_label = QLabel(f"Nom : {name}")
        self.layout.addWidget(self.name_label)

        # ✅ Bouton de statut (qui change de couleur)
        self.status_button = QPushButton("Statut : Inconnu")
        self.status_button.setStyleSheet("background-color: gray; color: white; font-weight: bold;")
        self.layout.addWidget(self.status_button)

        self.power_label = QLabel("Puissance : -")
        self.layout.addWidget(self.power_label)

        self.conso_label = QLabel("Consommation : -")
        self.layout.addWidget(self.conso_label)

        self.timestamp_label = QLabel("Date réception : -")
        self.layout.addWidget(self.timestamp_label)

        self.on_button = QPushButton("💡 Allumer")
        self.on_button.clicked.connect(self.allumer_prise)
        self.layout.addWidget(self.on_button)

        self.off_button = QPushButton("⛔ Éteindre")
        self.off_button.clicked.connect(self.eteindre_prise)
        self.layout.addWidget(self.off_button)

        self.setLayout(self.layout)

        self.client = mqtt.Client(protocol=mqtt.MQTTv5)
        self.client.username_pw_set(USERNAME, PASSWORD)
        self.client.tls_set(cert_reqs=ssl.CERT_NONE)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.init_mqtt()

    def init_mqtt(self):
        try:
            self.client.connect(BROKER, PORT, 60)
            self.client.loop_start()
        except Exception as e:
            self.status_button.setText(f"❌ Erreur connexion : {e}")
            self.status_button.setStyleSheet("background-color: gray; color: white;")

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.status_button.setText("✅ Connecté")
            client.subscribe(self.topic)
        else:
            self.status_button.setText(f"❌ Connexion échouée (code {rc})")
            self.status_button.setStyleSheet("background-color: gray; color: white;")

    def on_message(self, client, userdata, msg):
        try:
            payload_str = msg.payload.decode("utf-8")
            data = json.loads(payload_str)

            power = data.get("apower", "N/A")
            total_consumption_wh = data.get("total", "N/A")

            total_consumption_kwh = round(total_consumption_wh / 1000, 3) if total_consumption_wh != "N/A" else "N/A"

            self.power_label.setText(f"Puissance : {power} W")
            self.conso_label.setText(f"Consommation : {total_consumption_kwh} kWh")

            # ✅ Mise à jour du statut et désactivation des boutons
            if power != "N/A" and float(power) > 1:
                self.status_button.setText("🔴 Occupé")
                self.status_button.setStyleSheet("background-color: red; color: white; font-weight: bold;")
                self.on_button.setEnabled(False)
                self.off_button.setEnabled(True)
            else:
                self.status_button.setText("🟢 Libre")
                self.status_button.setStyleSheet("background-color: green; color: white; font-weight: bold;")
                self.on_button.setEnabled(True)
                self.off_button.setEnabled(False)

            self.timestamp_label.setText(f"Date réception : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as e:
            print(f"❌ Erreur lors de la réception : {e}")

    def allumer_prise(self):
        send_http_request(self.ip, turn_on=True)
        print(f"✅ La prise {self.name} a été allumée.")
        self.on_button.setEnabled(False)
        self.off_button.setEnabled(True)

    def eteindre_prise(self):
        send_http_request(self.ip, turn_on=False)
        print(f"✅ La prise {self.name} a été éteinte.")
        self.on_button.setEnabled(True)
        self.off_button.setEnabled(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = Dashboard()
    dashboard.show()
    sys.exit(app.exec())
