
import csv
from time import sleep, time

from pathlib import Path
import requests
from PyQt6.QtCore import QMutex, QThread, QWaitCondition, pyqtSignal
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from helpers.check import run_check


class WorkerThread(QThread):
    progress_update = pyqtSignal(int)
    speed_update = pyqtSignal(str)
    log_update = pyqtSignal(str)
    show_full_message = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()

    #parses details from UI thread to worker thread
    def details(self, collection_path, output_path, spare_quantity, log_box, items_per_sec):
        self.collection_path = collection_path
        self.output_path = output_path
        self.spare_quantity = int(spare_quantity)
        self.collection = []
        self.cards = []
        self.log = []
        self.log_box = log_box
        self.items_per_sec = items_per_sec

    #code for updating the log box in the UI    
    def update_log_box(self, text):
        self.log.append(text)
        self.log_update.emit(text)

    def update_progress(self, value):
        self.progress_update.emit(value)

    def update_speed(self, rate):
        text = f"{rate:.2f}"
        self.speed_update.emit(text)

    #code for resuming after maximum buylist was reached and emptied
    def resume(self):
        self.mutex.lock()
        self.wait_condition.wakeAll()
        self.mutex.unlock()

    #code that runs when worker thread is created    
    def run(self):

        run_check(csv_path=Path(self.collection_path), output=Path(self.output_path), debug=False, log_update=self.update_log_box, progress_update=self.update_progress, speed_update=self.update_speed)

 
