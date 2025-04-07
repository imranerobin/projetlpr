from PySide6 import QtWidgets
from PySide6 import QtGui


class MaFenetre(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.resize(300, 100)
        self.setWindowTitle("Dashboard")
        self.create_layouts()
        self.create_widgets()
        self.addWigets_to_layouts()
        self.setup_connections()

    def create_layouts(self):
        self.layoutV = QtWidgets.QVBoxLayout()
        self.layoutH0 = QtWidgets.QHBoxLayout()
        self.layoutH1 = QtWidgets.QHBoxLayout()
        self.layoutH2 = QtWidgets.QHBoxLayout()

    def create_widgets(self):
        self.radioBt_activer = QtWidgets.QRadioButton("Activer")
        self.radioBt_desactiver = QtWidgets.QRadioButton("Désctiver")
        self.lbl_Nom = QtWidgets.QLabel("Nom")
        self.LEdit_Nom = QtWidgets.QLineEdit()
        self.LEdit_Nom.setPlaceholderText("Saisir votre nom")
        self.btn_Effacer = QtWidgets.QPushButton("Effacer")
        self.btn_Quitter = QtWidgets.QPushButton("Quitter")
        self.radioBt_desactiver.setChecked(True)
        self.LEdit_Nom.setDisabled(True)

        self.lblImage = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap("Security-Camera.png")
        self.lblImage.setPixmap(pixmap)

    def addWigets_to_layouts(self):

        self.layoutH0.addWidget(self.radioBt_activer)
        self.layoutH0.addWidget(self.radioBt_desactiver)
        self.layoutH1.addWidget(self.lbl_Nom)
        self.layoutH1.addWidget(self.LEdit_Nom)
        self.layoutH2.addWidget(self.btn_Effacer)
        self.layoutH2.addWidget(self.btn_Quitter)

        self.layoutV.addLayout(self.layoutH0)
        self.layoutV.addLayout(self.layoutH1)
        self.layoutV.addLayout(self.layoutH2)
        self.layoutV.addWidget(self.lblImage)

        self.setLayout(self.layoutV)

    # def main_widget(self):
    #     self.widget = QtWidgets.QWidget(self)
    #     self.widget.setLayout(self.layoutV)
    #     self.setCentralWidget(self.widget)

    def setup_connections(self):
        self.btn_Quitter.clicked.connect(self.close)
        self.radioBt_activer.clicked.connect(self.activer)
        self.radioBt_desactiver.clicked.connect(self.desactiver)

    def activer(self):
        if self.radioBt_activer.isChecked():
            print("Activer")
            self.LEdit_Nom.setDisabled(False)

    def desactiver(self):
        if self.radioBt_desactiver.isChecked():
            print("Désactiver")
            self.LEdit_Nom.setDisabled(True)


app = QtWidgets.QApplication([])
form = MaFenetre()
form.show()
app.exec()