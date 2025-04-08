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

# Configuration MQTT
BROKER = "47567f9a74b445e6bef394abec5c83a1.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "ShellyPlusPlugS"
PASSWORD = "Ciel92110"

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard")
        self.setGeometry(100, 100, 1000, 500)

        self.layout = QVBoxLayout()

        self.add_button = QPushButton("Ajouter une prise Shelly")
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

        self.quit_button = QPushButton("Quitter l'application")
        self.quit_button.clicked.connect(self.close_application)
        self.layout.addWidget(self.quit_button)

        self.setLayout(self.layout)

    def ouvrir_formulaire(self):
        self.form_window = FormulaireWindow(self)
        self.form_window.show()

    def ajouter_prise(self, name, topic, localite):
        nouvelle_prise = ShellyWidget(name, topic, localite, self)
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

        self.name_label = QLabel("Nom de la prise Shelly :")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nom de la prise (ex: Prise Salon)")

        self.topic_label = QLabel("Topic MQTT :")
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("Topic MQTT (ex: shellyplusplugs-1234/rpc)")

        self.localite_label = QLabel("Localité :")
        self.localite_input = QLineEdit()
        self.localite_input.setPlaceholderText("Localité (ex: L-334.)")

        self.create_button = QPushButton("Ajouter")
        self.create_button.clicked.connect(self.creer_prise_shelly)

        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)
        layout.addWidget(self.topic_label)
        layout.addWidget(self.topic_input)
        layout.addWidget(self.localite_label)
        layout.addWidget(self.localite_input)
        layout.addWidget(self.create_button)

        self.setLayout(layout)

    def creer_prise_shelly(self):
        name = self.name_input.text().strip()
        topic = self.topic_input.text().strip()
        localite = self.localite_input.text().strip()

        # Vérification de doublons
        for i in range(self.dashboard.prises_layout.count()):
            widget = self.dashboard.prises_layout.itemAt(i).widget()
            if isinstance(widget, ShellyWidget):
                if widget.topic == topic:
                    print("❌ Ce topic est déjà utilisé. Veuillez en choisir un autre.")
                    return
                if widget.name == name:
                    print("❌ Ce nom est déjà utilisé. Veuillez en choisir un autre.")
                    return
                # if widget.localite == localite:
                #     print("❌ Cette localité est déjà utilisée. Veuillez en choisir une autre.")
                #     return

        if name and topic and localite:
            self.dashboard.ajouter_prise(name, topic, localite)
            self.close()
        else:
            print("❌ Veuillez remplir tous les champs.")

class ShellyWidget(QFrame):
    def __init__(self, name, topic, localite, dashboard):
        super().__init__()
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(2)

        self.name = name
        self.topic = topic
        self.localite = localite
        self.dashboard = dashboard

        self.layout = QVBoxLayout()

        self.image_label = QLabel()
        pixmap = QPixmap("prise2.png")
        pixmap = pixmap.scaled(120, 120)
        self.image_label.setPixmap(pixmap)
        self.layout.addWidget(self.image_label)

        self.name_label = QLabel(f"Nom : {name}")
        self.layout.addWidget(self.name_label)

        self.localite_label = QLabel(f"Localité : {localite}")
        self.layout.addWidget(self.localite_label)

        self.statut_label = QLabel("Statut : Inconnu")
        self.layout.addWidget(self.statut_label)

        self.power_label = QLabel("Puissance : -")
        self.layout.addWidget(self.power_label)

        self.conso_label = QLabel("Consommation : -")
        self.layout.addWidget(self.conso_label)

        self.on_button = QPushButton("Allumer")
        self.on_button.clicked.connect(self.allumer_prise)
        self.layout.addWidget(self.on_button)

        self.off_button = QPushButton("Éteindre")
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
            self.statut_label.setText(f"❌ Erreur de connexion : {e}")

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.statut_label.setText("✅ Connecté")
            client.subscribe(self.topic)
            if not self.topic.endswith("/test"):
                client.subscribe(self.topic.replace("/rpc", "/test"))
        else:
            self.statut_label.setText(f"❌ Connexion échouée (code {rc})")

    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload_str = msg.payload.decode("utf-8")
            data = json.loads(payload_str)

            power = data.get("apower", "N/A")
            total_consumption_wh = data.get("total", "N/A")
            total_consumption_kwh = round(total_consumption_wh / 1000, 3) if total_consumption_wh != "N/A" else "N/A"

            self.power_label.setText(f"Puissance : {power} W")
            self.conso_label.setText(f"Consommation : {total_consumption_kwh} kWh")

            if power != "N/A" and float(power) > 1:
                self.statut_label.setText("Statut : 🔴 Occupé")
                self.on_button.setDisabled(True)
                self.off_button.setDisabled(False)
                self.image_label.setPixmap(QPixmap("prise4.png").scaled(120, 120))
            else:
                self.statut_label.setText("Statut : 🟢 Libre")
                self.off_button.setDisabled(True)
                self.on_button.setDisabled(False)
                self.image_label.setPixmap(QPixmap("prise3.png").scaled(120, 120))

        except Exception as e:
            print(f"Erreur lors de la réception : {e}")

    def send_rpc_command(self, turn_on):
        message = {
            "id": 123,
            "src": "user_1",
            "method": "Switch.Set",
            "params": {
                "id": 0,
                "on": turn_on
            }
        }

        try:
            self.client.publish(self.topic, json.dumps(message), qos=1)
            print(f"📤 Commande MQTT envoyée à {self.topic} : {message}")
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi de la commande MQTT : {e}")

    def allumer_prise(self):
        self.send_rpc_command(True)

    def eteindre_prise(self):
        self.send_rpc_command(False)

    def supprimer_prise(self):
        print(f"La prise {self.name} a été supprimée")
        self.send_rpc_command(False)
        self.client.loop_stop()
        self.client.disconnect()
        self.dashboard.supprimer_prise(self)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = Dashboard()
    dashboard.show()
    sys.exit(app.exec())
