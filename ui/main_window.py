import configparser
import os

from PyQt6 import uic
from PyQt6.QtWidgets import QFileDialog, QMainWindow, QMessageBox

from workers.checker_worker import WorkerThread

#saved details of user for later            
config = configparser.ConfigParser()

#main UI window code
class MainWindow(QMainWindow):

    
    def __init__(self):
        #creates window
        super().__init__()
        uic.loadUi('ui/mainwindow.ui', self)
        self.resize(600, 450)
        self.setContentsMargins(20,20,20,20)

        #opens config file if it exists
        if os.path.exists("config.ini"):
            config.read("config.ini")
            self.usernameBox.setText(config["Info"]["username"])
            self.passwordBox.setText(config["Info"]["password"]) 
            self.collectionPath.setText(config["Info"]["path"]) 
            self.rememberBox.setChecked(True)

        # connects buttons
        self.addBuylistButton.pressed.connect(self.add_found_cards)
        self.browseButton.pressed.connect(self.browse_file)
    
    #for collection file browsing
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a File", "", "CSV Files (*.csv);;All Files (*)")
        if file_path:
            self.collectionPath.setText(file_path)

    #creating maximum buylist message        
    def max_reached(self):
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Maximum Buylist amount reached!")
        msg_box.setText("The maximum Buylist order size (300 cards) has been reached. Please submit this buylist order THEN push OK.")
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)

        #wait for OK to be pushed
        response = msg_box.exec()
        if response == QMessageBox.StandardButton.Ok:
            self.worker.resume()
    
    #runs the checking code when GO is pushed   
    def add_found_cards(self):
        username = self.usernameBox.text()
        password = self.passwordBox.text()
        spare_quantity = self.spareBox.text()
        collection_path = self.collectionPath.text()

        #saves config file if requested
        config["Info"] = {"username": username, "password": password, "path": collection_path}
        if self.rememberBox.isChecked():
            with open("config.ini", "w") as configfile:
                config.write(configfile)

        #creates the worker thread and runs code with details given
        self.worker = WorkerThread()
        self.worker.details(username,
                            password,
                            collection_path,
                            spare_quantity,
                            self.logBox,
                            self.itemsPerSec)
        self.worker.progress_update.connect(self.progressBar.setValue)
        self.worker.log_update.connect(self.update_log)
        self.worker.speed_update.connect(self.update_speed)
        self.worker.show_full_message.connect(self.max_reached)
        self.worker.start()

    def update_log(self, text):
        self.logBox.setText(
            self.logBox.text() + "\n" + text
        )

    def update_speed(self, speed):
        self.itemsPerSec.setText(f"{speed} items per second.")