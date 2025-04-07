import sys
import ssl
import json
import paho.mqtt.client as mqtt
from datetime import datetime

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QScrollArea, QFrame
)
from PySide6.QtCore import Qt
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
        self.setGeometry(100, 100, 1000, 500)

        self.layout = QVBoxLayout()
        self.add_button = QPushButton("➕ Ajouter une prise Shelly")
        self.add_button.clicked.connect(self.ouvrir_formulaire)
        self.layout.addWidget(self.add_button)

        self.prises_layout = QHBoxLayout()
        self.scroll_content = QWidget()
        self.scroll_content.setLayout(self.prises_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)

        self.quit_button = QPushButton("❌ Quitter l'application")
        self.quit_button.clicked.connect(self.close_application)
        self.layout.addWidget(self.quit_button)

        self.setLayout(self.layout)

    def ouvrir_formulaire(self):
        self.form_window = FormulaireWindow(self)
        self.form_window.show()

    def ajouter_prise(self, name, topic, ip):
        nouvelle_prise = ShellyWidget(name, topic, ip, self)
        self.prises_layout.addWidget(nouvelle_prise)
        self.scroll_content.adjustSize()

    def supprimer_prise(self, prise):
        self.prises_layout.removeWidget(prise)
        prise.deleteLater()
        self.scroll_content.adjustSize()

    def close_application(self):
        QApplication.quit()

class FormulaireWindow(QWidget):
    def __init__(self, dashboard):
        super().__init__()
        self.dashboard = dashboard
        self.setWindowTitle("Formulaire - Ajouter Prise Shelly")
        self.setGeometry(150, 150, 400, 200)

        layout = QVBoxLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nom de la prise (ex: Prise Salon)")
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("Topic MQTT (ex: shellyplusplugs-1234/test)")
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Adresse IP (ex: 192.168.1.101)")

        self.create_button = QPushButton("Ajouter")
        self.create_button.clicked.connect(self.creer_prise_shelly)

        layout.addWidget(QLabel("Nom de la prise :"))
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Topic MQTT :"))
        layout.addWidget(self.topic_input)
        layout.addWidget(QLabel("Adresse IP :"))
        layout.addWidget(self.ip_input)
        layout.addWidget(self.create_button)

        self.setLayout(layout)

    def creer_prise_shelly(self):
        name = self.name_input.text().strip()
        topic = self.topic_input.text().strip()
        ip = self.ip_input.text().strip()

        if name and topic and ip:
            self.dashboard.ajouter_prise(name, topic, ip)
            self.close()
        else:
            print("❌ Veuillez remplir tous les champs.")

class ShellyWidget(QFrame):
    def __init__(self, name, topic, ip, dashboard):
        super().__init__()
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(2)

        self.name = name
        self.topic = topic
        self.ip = ip
        self.dashboard = dashboard

        self.last_total_consumption = None
        self.last_timestamp = None

        self.layout = QVBoxLayout()
        pixmap = QPixmap("prise2.png").scaled(120, 120)
        self.image_label = QLabel()
        self.image_label.setPixmap(pixmap)
        self.layout.addWidget(self.image_label)

        self.name_label = QLabel(f"Nom : {name}")
        self.statut_label = QLabel("Statut : Inconnu")
        self.power_label = QLabel("Puissance : -")
        self.conso_label = QLabel("Conso 1h : -")
        self.timestamp_label = QLabel("Date réception : -")

        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.statut_label)
        self.layout.addWidget(self.power_label)
        self.layout.addWidget(self.conso_label)
        self.layout.addWidget(self.timestamp_label)

        self.on_button = QPushButton("💡 Allumer")
        self.on_button.clicked.connect(self.allumer_prise)
        self.layout.addWidget(self.on_button)

        self.off_button = QPushButton("⛔ Éteindre")
        self.off_button.clicked.connect(self.eteindre_prise)
        self.layout.addWidget(self.off_button)

        self.delete_button = QPushButton("🗑️ Supprimer")
        self.delete_button.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        self.delete_button.clicked.connect(self.supprimer_prise)
        self.layout.addWidget(self.delete_button)

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
            self.statut_label.setText(f"❌ Erreur : {e}")

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.statut_label.setText("✅ Connecté")
            client.subscribe(self.topic)
        else:
            self.statut_label.setText(f"❌ Connexion échouée (code {rc})")

    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8"))
            total_consumption_wh = data.get("total", "N/A")

            if total_consumption_wh != "N/A":
                now = datetime.now()
                if self.last_total_consumption is not None and self.last_timestamp is not None:
                    time_diff = (now - self.last_timestamp).total_seconds() / 3600
                    if time_diff > 0:
                        hourly_kwh = round((total_consumption_wh - self.last_total_consumption) / 1000 / time_diff, 3)
                        self.conso_label.setText(f"Conso 1h : {hourly_kwh} kWh")

                self.last_total_consumption = total_consumption_wh
                self.last_timestamp = now

            self.power_label.setText(f"Puissance : {data.get('apower', 'N/A')} W")

        except Exception as e:
            print(f"❌ Erreur réception : {e}")

    def allumer_prise(self):
        send_http_request(self.ip, turn_on=True)

    def eteindre_prise(self):
        send_http_request(self.ip, turn_on=False)

    def supprimer_prise(self):
        self.eteindre_prise()
        self.client.loop_stop()
        self.client.disconnect()
        self.dashboard.supprimer_prise(self)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = Dashboard()
    dashboard.show()
    sys.exit(app.exec())
