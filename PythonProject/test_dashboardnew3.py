import sys
import ssl
import json
import paho.mqtt.client as mqtt
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

    def ajouter_prise(self, name, localite, id, topic):
        self.prise_options = PriseOptionsWindow(name, localite, id, topic, self)
        self.prise_options.show()

    def afficher_info_prise(self, name, localite, topic, puissance):
        info_prise_label = QLabel(f"{name} ({localite}) - Topic: {topic} - Puissance: {puissance}W")
        self.prises_layout.addWidget(info_prise_label)

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
            self.dashboard.ajouter_prise(name, localite, id, None)  # On passe None ici pour topic
            self.close()
        else:
            print("❌ Veuillez remplir tous les champs.")


class PriseOptionsWindow(QWidget):
    def __init__(self, name, localite, id, topic, dashboard):
        super().__init__()
        self.setWindowTitle(f"Options - {name}")
        self.setGeometry(200, 200, 300, 150)
        self.dashboard = dashboard
        self.name = name
        self.localite = localite
        self.id = id
        self.topic = topic

        layout = QVBoxLayout()

        self.valeur_button = QPushButton("Valeur")
        self.gestion_button = QPushButton("Gestion")

        self.valeur_button.clicked.connect(self.ouvrir_valeur_window)
        self.gestion_button.clicked.connect(self.gestion_prise)

        layout.addWidget(self.valeur_button)
        layout.addWidget(self.gestion_button)

        self.setLayout(layout)

    def ouvrir_valeur_window(self):
        self.valeur_window = ValeurWindow(self.name, self.localite, self.id, self.topic, self)
        self.valeur_window.show()

    def gestion_prise(self):
        print("Gestion de la prise")
        # Ici tu peux ajouter le code pour gérer la prise


class ValeurWindow(QWidget):
    def __init__(self, name, localite, id, topic, prise_options_window):
        super().__init__()
        self.setWindowTitle(f"Valeurs - {name}")
        self.setGeometry(250, 250, 400, 200)

        self.prise_options_window = prise_options_window  # Référence vers la fenêtre des options de prise
        self.id = id  # Conserver l'ID de la prise
        self.topic = topic  # Le topic est également passé ici
        layout = QVBoxLayout()

        self.topic_label = QLabel(f"Topic MQTT actuel : {topic if topic else 'Non défini'}")
        self.info_label = QLabel("Entrez le Topic MQTT pour récupérer les valeurs.")

        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("Entrez le topic_saisie ici")

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.saisir_topic)

        layout.addWidget(self.topic_label)
        layout.addWidget(self.info_label)
        layout.addWidget(self.topic_input)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

    def saisir_topic(self):
        topic_saisie = self.topic_input.text().strip()
        if topic_saisie:
            # Construction du topic avec l'ID et le topic_saisie
            topic = f"ShellyPlusPlugS-{self.id}/{topic_saisie}"
            self.topic_label.setText(f"Topic MQTT : {topic}")
            self.info_label.setText("Topic défini. Vous pouvez maintenant récupérer les valeurs.")

            # Mise à jour du topic dans la fenêtre parente
            self.prise_options_window.topic = topic

            # Connexion au broker MQTT et récupérer la puissance
            self.client = mqtt.Client()
            self.client.username_pw_set(USERNAME, PASSWORD)
            self.client.tls_set_context(ssl.create_default_context())

            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message

            self.client.connect(BROKER, PORT)
            self.client.loop_start()

        else:
            print("❌ Veuillez entrer un topic valide.")

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connexion réussie avec le code de résultat {rc}")
        # Subcrire au topic pour récupérer la puissance
        client.subscribe(self.topic)

    def on_message(self, client, userdata, msg):
        print(f"Message reçu sur le topic {msg.topic}: {msg.payload.decode()}")
        try:
            data = json.loads(msg.payload.decode())
            puissance = data.get('power', 'Non disponible')
            print(f"Puissance : {puissance}W")
            # Afficher la puissance dans la fenêtre Dashboard
            self.prise_options_window.dashboard.afficher_info_prise(self.prise_options_window.name,
                                                                    self.prise_options_window.localite,
                                                                    self.topic,
                                                                    puissance)
        except json.JSONDecodeError:
            print("Erreur lors du décodage des données MQTT.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = Dashboard()
    dashboard.show()
    sys.exit(app.exec())
