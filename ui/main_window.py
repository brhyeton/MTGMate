import configparser
import os

from PyQt6 import uic
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QFileDialog, QMainWindow, QMessageBox

from workers.checker_worker import WorkerThread

import helpers.config
from pathlib import Path

#main UI window code
class MainWindow(QMainWindow):

    
    def __init__(self):
        #creates window
        super().__init__()
        uic.loadUi('ui/mainwindow.ui', self)
        self.resize(600, 450)
        self.setContentsMargins(20,20,20,20)

        # connects buttons
        self.runButton.pressed.connect(self.check_buylist)
        self.browseButton.pressed.connect(self.browse_file)
        self.stopButton.pressed.connect(self.stop_check)

        self.settings = QSettings("MTGMateTool", "Buylist Checker")
        self.load_settings()
        self.rememberBox.stateChanged.connect(self.handle_remember_toggle)
    
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
    
    #runs the checking code when Run is pushed   
    def check_buylist(self):
        spare_quantity = self.spareBox.text()
        collection_path = Path(self.collectionPath.text())
        output_path = helpers.config._HERE / Path(self.outputPath.text())

        #creates the worker thread and runs code with details given
        self.worker = WorkerThread()
        self.worker.details(collection_path,
                            output_path,
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

    def stop_check(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            self.update_log("Check process stopped.")

    def load_settings(self):
        """Restore saved values if 'Remember' was previously checked."""
        remember_checked = self.settings.value("rememberBox", False, type=bool)
        self.rememberBox.setChecked(remember_checked)

        if remember_checked:
            self.collectionPath.setText(self.settings.value("collectionPath", "", type=str))
            self.outputPath.setText(self.settings.value("outputPath", "", type=str))
            self.addAlongsideBox.setChecked(self.settings.value("addAlongsideBox", False, type=bool))
            
            # spareBox is a QSpinBox, so load as an integer
            self.spareBox.setValue(self.settings.value("spareBox", 0, type=int))

    def save_settings(self):
        """Save settings if rememberBox is checked, otherwise wipe them."""
        is_remembered = self.rememberBox.isChecked()
        self.settings.setValue("rememberBox", is_remembered)

        if is_remembered:
            self.settings.setValue("collectionPath", self.collectionPath.text())
            self.settings.setValue("outputPath", self.outputPath.text())
            self.settings.setValue("addAlongsideBox", self.addAlongsideBox.isChecked())
            
            # Save the spinbox's numeric value
            self.settings.setValue("spareBox", self.spareBox.value())
        else:
            # Wipe stored data if the user unchecks the box
            self.settings.remove("collectionPath")
            self.settings.remove("outputPath")
            self.settings.remove("addAlongsideBox")
            self.settings.remove("spareBox")

    def handle_remember_toggle(self, state):
        self.save_settings()

    def closeEvent(self, event):
        """Ensure settings are updated right as the app closes."""
        self.save_settings()
        event.accept()