import sys
import ssl
import json
import paho.mqtt.client as mqtt
from datetime import datetime
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit

# Configuration MQTT
BROKER = "47567f9a74b445e6bef394abec5c83a1.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "ShellyPlusPlugS"
PASSWORD = "Ciel92110"

# Dashboard principal
class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard")
        self.setGeometry(100, 100, 400, 200)

        layout = QVBoxLayout()

        self.add_button = QPushButton("➕ Ajouter une prise Shelly")
        self.add_button.clicked.connect(self.ouvrir_formulaire)
        layout.addWidget(self.add_button)

        self.setLayout(layout)

    def ouvrir_formulaire(self):
        self.form_window = FormulaireWindow()
        self.form_window.show()

# Fenêtre pour saisir les informations de la prise Shelly
class FormulaireWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Formulaire - Ajouter Prise Shelly")
        self.setGeometry(150, 150, 400, 250)

        layout = QVBoxLayout()

        self.name_label = QLabel("Nom de la prise Shelly :")
        layout.addWidget(self.name_label)

        self.name_input = QLineEdit(self)
        layout.addWidget(self.name_input)

        self.id_label = QLabel("ID de la prise Shelly :")
        layout.addWidget(self.id_label)

        self.id_input = QLineEdit(self)
        layout.addWidget(self.id_input)

        self.topic_label = QLabel("Topic MQTT :")
        layout.addWidget(self.topic_label)

        self.topic_input = QLineEdit(self)
        layout.addWidget(self.topic_input)

        self.ip_label = QLabel("Adresse IP :")
        layout.addWidget(self.ip_label)

        self.ip_input = QLineEdit(self)
        layout.addWidget(self.ip_input)

        self.create_button = QPushButton("Créer")
        self.create_button.clicked.connect(self.creer_prise_shelly)
        layout.addWidget(self.create_button)

        self.setLayout(layout)

    def creer_prise_shelly(self):
        name = self.name_input.text()
        prise_id = self.id_input.text()
        topic = self.topic_input.text()
        ip = self.ip_input.text()

        if name and prise_id and topic and ip:
            self.prise_window = ShellyWindow(name, prise_id, topic, ip)
            self.prise_window.show()
            self.close()  # Ferme le formulaire
        else:
            print("❌ Veuillez remplir tous les champs.")

# Fenêtre de suivi de la prise Shelly
class ShellyWindow(QWidget):
    def __init__(self, name, prise_id, topic, ip):
        super().__init__()
        self.setWindowTitle(f"Infos Prise Shelly - {name}")
        self.setGeometry(150, 150, 400, 300)

        self.layout = QVBoxLayout()

        self.status_label = QLabel("Connexion en cours...")
        self.layout.addWidget(self.status_label)

        self.name_label = QLabel(f"Nom : {name}")
        self.layout.addWidget(self.name_label)

        self.prise1_label = QLabel(f"ID Prise : {prise_id}")
        self.layout.addWidget(self.prise1_label)

        self.ip_label = QLabel(f"IP : {ip}")
        self.layout.addWidget(self.ip_label)

        self.topic_label = QLabel(f"Topic : {topic}")
        self.layout.addWidget(self.topic_label)

        self.power_label = QLabel("Puissance : -")
        self.layout.addWidget(self.power_label)

        self.voltage_label = QLabel("Tension : -")
        self.layout.addWidget(self.voltage_label)

        self.conso_label = QLabel("Consommation : -")
        self.layout.addWidget(self.conso_label)

        self.timestamp_label = QLabel("Date réception : -")
        self.layout.addWidget(self.timestamp_label)

        # Bouton supprimer prise
        self.delete_button = QPushButton("❌ Supprimer la prise Shelly")
        self.delete_button.clicked.connect(self.supprimer_prise_shelly)
        self.layout.addWidget(self.delete_button)

        self.setLayout(self.layout)

        # Initialisation client MQTT
        self.client = mqtt.Client(protocol=mqtt.MQTTv5)
        self.client.username_pw_set(USERNAME, PASSWORD)
        self.client.tls_set(cert_reqs=ssl.CERT_NONE)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.init_mqtt()

        # Sauvegarder les informations de la prise
        self.name = name
        self.prise_id = prise_id
        self.topic = topic
        self.ip = ip

    def init_mqtt(self):
        try:
            self.client.connect(BROKER, PORT, 60)
            self.client.loop_start()
        except Exception as e:
            self.status_label.setText(f"❌ Erreur de connexion : {e}")

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.status_label.setText("✅ Connecté au broker MQTT")
            # S'abonner au topic dynamique basé sur l'ID de la prise
            client.subscribe(self.topic)
        else:
            self.status_label.setText(f"❌ Connexion échouée (code {rc})")

    def on_message(self, client, userdata, msg):
        try:
            # Log complet dans la console
            payload_str = msg.payload.decode("utf-8")

            log_message = (
                f"Log MQTT : Received PUBLISH (d0, q0, r0, m0), '{msg.topic}', "
                f"...  ({len(payload_str)} bytes)"
            )
            print(log_message)

            print(f"Message reçu sur le topic {msg.topic}: {payload_str}")

            # Charger les données JSON
            data = json.loads(payload_str)

            power = data.get("apower", "N/A")
            voltage = data.get("current", "N/A")
            total_consumption_wh = data.get("total", "N/A")

            if total_consumption_wh != "N/A":
                total_consumption_kwh = round(total_consumption_wh / 1000, 3)
            else:
                total_consumption_kwh = "N/A"

            # Mise à jour de l'interface graphique
            self.power_label.setText(f"Puissance : {power} W")
            self.voltage_label.setText(f"Tension : {voltage} V")
            self.conso_label.setText(f"Consommation : {total_consumption_kwh} kWh")

            # Mise à jour de l'état de la prise
            if power != "N/A" and float(power) > 1:  # Seuil de 1 W pour considérer que la prise est occupée
                self.prise1_label.setText(f"Prise {self.prise_id} : Occupée")
            else:
                self.prise1_label.setText(f"Prise {self.prise_id} : Libre")

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.timestamp_label.setText(f"Date réception : {current_time}")

        except Exception as e:
            print(f"❌ Erreur lors de la lecture du message : {e}")

    def supprimer_prise_shelly(self):
        # Fonction pour fermer la fenêtre et "supprimer" la prise Shelly
        print(f"❌ Prise {self.prise_id} supprimée.")
        self.close()

# Lancer l'application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = Dashboard()
    dashboard.show()
    sys.exit(app.exec())
