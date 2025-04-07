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

def send_http_request(id, turn_on):
    url = f"http://shelly-device.local/{id}/relay/0?turn={'on' if turn_on else 'off'}"
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

        self.add_button = QPushButton(" Ajouter une prise Shelly")
        self.add_button.clicked.connect(self.ouvrir_formulaire)
        self.layout.addWidget(self.add_button)

        self.prises_layout = QHBoxLayout()
        self.scroll_content = QWidget()
        self.scroll_content.setLayout(self.prises_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidget(self.scroll_content)

        self.layout.addWidget(self.scroll_area)

        self.quit_button = QPushButton(" Quitter l'application")
        self.quit_button.clicked.connect(self.close_application)
        self.layout.addWidget(self.quit_button)

        self.setLayout(self.layout)

    def ouvrir_formulaire(self):
        self.form_window = FormulaireWindow(self)
        self.form_window.show()

    def ajouter_prise(self, name, localite, id):
        self.prise_options = PriseOptionsWindow(name, localite, id, self)
        self.prise_options.show()

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

        self.name_label = QLabel("Nom de la prise Shelly :")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nom de la prise (ex: Prise Salon)")

        self.localite_label = QLabel("Localité :")
        self.localite_input = QLineEdit()
        self.localite_input.setPlaceholderText("Localité (ex: Salle L334)")

        self.id_label = QLabel("ID de la prise :")
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("ID de la prise (ex: shellyplusplugs-1234)")

        self.create_button = QPushButton("Ajouter")
        self.create_button.clicked.connect(self.creer_prise_shelly)

        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)
        layout.addWidget(self.localite_label)
        layout.addWidget(self.localite_input)
        layout.addWidget(self.id_label)
        layout.addWidget(self.id_input)
        layout.addWidget(self.create_button)

        self.setLayout(layout)

    def creer_prise_shelly(self):
        name = self.name_input.text().strip()
        localite = self.localite_input.text().strip()
        id = self.id_input.text().strip()

        if name and localite and id:
            self.dashboard.ajouter_prise(name, localite, id)
            self.close()
        else:
            print("❌ Veuillez remplir tous les champs.")


class PriseOptionsWindow(QWidget):
    def __init__(self, name, localite, id, dashboard):
        super().__init__()
        self.setWindowTitle(f"Options - {name}")
        self.setGeometry(200, 200, 300, 150)
        self.dashboard = dashboard
        self.name = name
        self.localite = localite
        self.id = id

        layout = QVBoxLayout()

        self.valeur_button = QPushButton("Valeur")
        self.gestion_button = QPushButton("Gestion")

        self.valeur_button.clicked.connect(self.ouvrir_valeur_window)
        self.gestion_button.clicked.connect(lambda: self.dashboard.ajouter_prise(name, localite, id))

        layout.addWidget(self.valeur_button)
        layout.addWidget(self.gestion_button)

        self.setLayout(layout)

    def ouvrir_valeur_window(self):
        self.valeur_window = ValeurWindow(self.name, self.localite, self.id)
        self.valeur_window.show()


class ValeurWindow(QWidget):
    def __init__(self, name, localite, id):
        super().__init__()
        self.setWindowTitle(f"Valeurs - {name}")
        self.setGeometry(250, 250, 400, 200)

        self.name = name
        self.localite = localite
        self.id = id
        self.topic = ""

        self.layout = QVBoxLayout()

        self.topic_label = QLabel("Entrez le topic MQTT :")
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("Ex: shellyplusplugs-64b7080cdc04/test")

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.recuperer_valeurs)

        self.value_label = QLabel("Valeur reçue : ---")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("font-size: 18px; color: green;")

        self.layout.addWidget(self.topic_label)
        self.layout.addWidget(self.topic_input)
        self.layout.addWidget(self.ok_button)
        self.layout.addWidget(self.value_label)

        self.setLayout(self.layout)

        # Configuration client MQTT
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.username_pw_set(USERNAME, PASSWORD)
        self.mqtt_client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

    def recuperer_valeurs(self):
        self.topic = self.topic_input.text().strip()
        if self.topic:
            try:
                print(f"🔌 Connexion au broker MQTT...")
                self.mqtt_client.connect(BROKER, PORT, 60)
                self.mqtt_client.loop_start()
            except Exception as e:
                print(f"❌ Erreur lors de la connexion MQTT : {e}")
        else:
            print("❌ Veuillez entrer un topic valide.")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Connecté au broker MQTT")
            self.mqtt_client.subscribe(self.topic)
            print(f"📡 Abonné au topic : {self.topic}")
        else:
            print(f"❌ Erreur de connexion au broker MQTT. Code : {rc}")

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        print(f"📨 Message reçu sur {msg.topic} : {payload}")
        self.value_label.setText(f"Valeur reçue : {payload}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = Dashboard()
    dashboard.show()
    sys.exit(app.exec())
