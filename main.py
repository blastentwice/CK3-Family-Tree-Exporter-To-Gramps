import sys
import configparser
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
    QFileDialog, QTextEdit, QInputDialog, QComboBox, QLineEdit, QMessageBox
from PySide6.QtCore import QThread, Signal, QObject
from PySide6.QtGui import QTextCursor,QFont
from io import StringIO
import loading_text as lt
import character as chr
import traceback


class OutputRedirector(QObject):
    outputWritten = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buffer = StringIO()

    def write(self, text):
        self._buffer.write(text)
        self.outputWritten.emit(text)

    def flush(self):
        pass

class ConversionWorker(QThread):
    error = Signal(str)
    log = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, input_file, output_file, main_id=None, conversion_type='json'):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.main_id = main_id
        self.conversion_type = conversion_type

    def run(self):

        try:
            if self.conversion_type == 'json':
                self.log.emit("\nStarting conversion to JSON...")
                lt.to_json(self.input_file, self.output_file)
                self.log.emit("JSON conversion completed.")

            else:
                self.log.emit("\nLoading game data...")
                data, yaml_data = lt.Load().loading_main(self.input_file)
                self.log.emit("Processing character data...")
                chr.char_main(data, yaml_data, self.main_id, self.output_file)
                self.log.emit("\nCSV conversion completed.")

            self.finished.emit(True, self.output_file)
        except Exception:
            error_info = traceback.format_exc()
            self.error.emit(error_info)
            self.finished.emit(False, "")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CK3 to Gramps Converter")
        self.setGeometry(100, 100, 600, 400)

        self.config = configparser.ConfigParser()
        self.config.read('config.ini')

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # Set up output redirection
        self.output_redirector = OutputRedirector()
        self.output_redirector.outputWritten.connect(self.append_log)
        sys.stdout = self.output_redirector

        # CK3 Directory
        ck3_layout = QHBoxLayout()
        self.ck3_label = QLabel("CK3 Directory:")
        self.ck3_path = QLineEdit(self.config['Default']['CK3 DIRECTORY'])
        self.ck3_button = QPushButton("Browse")
        self.ck3_button.clicked.connect(self.browse_ck3)
        ck3_layout.addWidget(self.ck3_label)
        ck3_layout.addWidget(self.ck3_path)
        ck3_layout.addWidget(self.ck3_button)
        layout.addLayout(ck3_layout)

        # Save File
        save_layout = QHBoxLayout()
        self.save_label = QLabel("Save File:")
        self.save_path = QLineEdit(self.config['Default']['GAME SAVE DIRECTORY'])
        self.save_button = QPushButton("Browse")
        self.save_button.clicked.connect(self.browse_save)
        save_layout.addWidget(self.save_label)
        save_layout.addWidget(self.save_path)
        save_layout.addWidget(self.save_button)
        layout.addLayout(save_layout)

        # JSON File
        json_layout = QHBoxLayout()
        self.json_label = QLabel("JSON File:")
        self.json_path = QLineEdit(self.config['Default']['JSON DIRECTORY'])
        self.json_button = QPushButton("Browse")
        self.json_button.clicked.connect(self.browse_json)
        json_layout.addWidget(self.json_label)
        json_layout.addWidget(self.json_path)
        json_layout.addWidget(self.json_button)
        layout.addLayout(json_layout)

        # Conversion buttons
        button_layout = QHBoxLayout()
        self.json_button = QPushButton("Convert to JSON")
        self.json_button.clicked.connect(self.convert_to_json)
        self.csv_button = QPushButton("Convert to CSV")
        self.csv_button.clicked.connect(self.convert_to_csv)
        button_layout.addWidget(self.json_button)
        button_layout.addWidget(self.csv_button)
        layout.addLayout(button_layout)

        # Log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

    def append_log(self, text):
        self.log_output.moveCursor(QTextCursor.End)
        self.log_output.insertPlainText(text)
        self.log_output.moveCursor(QTextCursor.End)

    def browse_ck3(self):
        directory = QFileDialog.getExistingDirectory(self, "Select CK3 Directory")
        if directory:
            self.ck3_path.setText(directory)
            self.config['Default']['CK3 DIRECTORY'] = directory
            self.save_config()

    def browse_save(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Save File", "", "CK3 Save Files (*.ck3)")
        if file:
            self.save_path.setText(file)
            self.config['Default']['GAME SAVE DIRECTORY'] = file
            self.save_config()

    def browse_json(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select JSON File", "", "JSON Files (*.json)")
        if file:
            self.json_path.setText(file)
            self.config['Default']['JSON DIRECTORY'] = file
            self.save_config()
    # disabled for now
   # def save_language(self, language):
   #     self.config['Default']['LANGUAGE'] = language
    #    self.save_config()

    def save_config(self):
        with open('./config.ini', 'w') as configfile:
            self.config.write(configfile)

    def convert_to_json(self):
        input_file = self.save_path.text()
        if not input_file:
            QMessageBox.warning(self, "No Save File", "Please select a CK3 save file first.")
            return

        # Set default output path
        default_output = input_file.rsplit('.', 1)[0] + '.json'
        output_file, _ = QFileDialog.getSaveFileName(self, "Save JSON File", default_output, "JSON Files (*.json)")
        if output_file:
            self.start_conversion(input_file, output_file, conversion_type='json')

    def convert_to_csv(self):
        input_file = self.json_path.text()
        if not input_file:
            QMessageBox.warning(self, "No JSON File", "Please select a JSON file first.")
            return

        main_id, ok = QInputDialog.getText(self, "Enter Main ID", "Please enter the main character ID:")
        if ok and main_id:
            # Set default output path
            default_output = input_file.rsplit('.', 1)[0] + '.csv'
            output_file, _ = QFileDialog.getSaveFileName(self, "Save CSV File", default_output, "CSV Files (*.csv)")
            if output_file:
                self.start_conversion(input_file, output_file, main_id, conversion_type='csv')

    def start_conversion(self, input_file, output_file, main_id=None, conversion_type='json'):
        self.worker = ConversionWorker(input_file, output_file, main_id, conversion_type)
        self.worker.error.connect(self.show_error)
        self.worker.log.connect(self.log_message)
        self.worker.finished.connect(self.conversion_finished)
        self.worker.start()

        self.json_button.setEnabled(False)
        self.csv_button.setEnabled(False)

    def log_message(self, message):
        print(message)

    def show_error(self, error_message):
        self.log_output.append(f"Error: {error_message}")

    def set_json_path(self, path):
        self.json_path.setText(path)

    def conversion_finished(self, success, output_file):
        if success:
            self.log_output.append("Conversion completed successfully!")
            QMessageBox.information(self, "Success", "Conversion completed successfully!")
            if output_file.lower().endswith('.json'):
                self.set_json_path(output_file)
                self.config['Default']['JSON DIRECTORY'] = output_file
                self.save_config()
        else:
            self.log_output.append("Conversion failed. Check the above traceback for details.")

        self.json_button.setEnabled(True)
        self.csv_button.setEnabled(True)

if __name__ == "__main__":

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())