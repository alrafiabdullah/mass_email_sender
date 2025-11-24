import sys
import json
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QTextEdit,
    QFileDialog,
    QProgressBar,
    QMessageBox,
    QGroupBox,
    QSpinBox,
    QCheckBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
)

from utils import load_csv, send_emails, validate_email_settings


class SettingsWidget(QWidget):
    """Settings tab for email configuration"""

    def __init__(self):
        super().__init__()
        # Use user's home directory for settings file
        self.settings_file = Path.home() / ".mass_email_sender" / "email_settings.json"
        # Create directory if it doesn't exist
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout()

        # SMTP Settings Group
        smtp_group = QGroupBox("SMTP Server Settings")
        smtp_layout = QVBoxLayout()

        # SMTP Server
        server_layout = QHBoxLayout()
        server_layout.addWidget(QLabel("SMTP Server:"))
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("smtp.gmail.com")
        server_layout.addWidget(self.server_input)
        smtp_layout.addLayout(server_layout)

        # Port
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(587)
        port_layout.addWidget(self.port_input)
        port_layout.addStretch()
        smtp_layout.addLayout(port_layout)

        # Use TLS
        self.tls_checkbox = QCheckBox("Use TLS/STARTTLS")
        self.tls_checkbox.setChecked(True)
        smtp_layout.addWidget(self.tls_checkbox)

        smtp_group.setLayout(smtp_layout)
        layout.addWidget(smtp_group)

        # Credentials Group
        creds_group = QGroupBox("Email Credentials")
        creds_layout = QVBoxLayout()

        # Email
        email_layout = QHBoxLayout()
        email_layout.addWidget(QLabel("Email:"))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("your.email@example.com")
        email_layout.addWidget(self.email_input)
        creds_layout.addLayout(email_layout)

        # Password
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("App password or account password")
        password_layout.addWidget(self.password_input)
        creds_layout.addLayout(password_layout)

        creds_group.setLayout(creds_layout)
        layout.addWidget(creds_group)

        # Save button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)

        layout.addStretch()
        self.setLayout(layout)

    def get_settings(self):
        """Return current settings as dictionary"""
        return {
            "smtp_server": self.server_input.text(),
            "smtp_port": self.port_input.value(),
            "use_tls": self.tls_checkbox.isChecked(),
            "sender_email": self.email_input.text(),
            "sender_password": self.password_input.text(),
        }

    def save_settings(self):
        """Save settings to file"""
        settings = self.get_settings()
        try:
            with open(self.settings_file, "w") as f:
                json.dump(settings, f, indent=2)
            QMessageBox.information(self, "Success", "Settings saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")

    def load_settings(self):
        """Load settings from file"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r") as f:
                    settings = json.load(f)

                self.server_input.setText(settings.get("smtp_server", ""))
                self.port_input.setValue(settings.get("smtp_port", 587))
                self.tls_checkbox.setChecked(settings.get("use_tls", True))
                self.email_input.setText(settings.get("sender_email", ""))
                self.password_input.setText(settings.get("sender_password", ""))
            except Exception as e:
                print(f"Failed to load settings: {e}")


class EmailThread(QThread):
    """Thread for sending emails without blocking UI"""

    progress = pyqtSignal(int, int, str)  # current, total, message
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, recipients, subject, body_template, settings):
        super().__init__()
        self.recipients = recipients
        self.subject = subject
        self.body_template = body_template
        self.settings = settings

    def run(self):
        try:
            send_emails(
                self.recipients,
                self.subject,
                self.body_template,
                self.settings,
                self.progress,
            )
            self.finished.emit(
                True, f"Successfully sent {len(self.recipients)} emails!"
            )
        except Exception as e:
            self.finished.emit(False, f"Error sending emails: {str(e)}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.recipients = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Mass Email Sender")
        self.setMinimumSize(800, 600)

        # Central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Create tabs
        tabs = QTabWidget()

        # Email composition tab
        email_tab = QWidget()
        email_layout = QVBoxLayout()

        # CSV Upload section
        csv_group = QGroupBox("1. Upload CSV File")
        csv_layout = QHBoxLayout()

        self.csv_label = QLabel("No file selected")
        csv_layout.addWidget(self.csv_label)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_csv)
        csv_layout.addWidget(browse_btn)

        csv_group.setLayout(csv_layout)
        email_layout.addWidget(csv_group)

        # Recipients preview
        preview_group = QGroupBox("Recipients Preview")
        preview_layout = QVBoxLayout()

        self.recipients_table = QTableWidget()
        self.recipients_table.setColumnCount(3)
        self.recipients_table.setHorizontalHeaderLabels(
            ["Email", "First Name", "Last Name"]
        )
        self.recipients_table.setMaximumHeight(150)
        preview_layout.addWidget(self.recipients_table)

        self.recipients_count_label = QLabel("No recipients loaded")
        preview_layout.addWidget(self.recipients_count_label)

        preview_group.setLayout(preview_layout)
        email_layout.addWidget(preview_group)

        # Email composition section
        compose_group = QGroupBox("2. Compose Email")
        compose_layout = QVBoxLayout()

        # Subject
        subject_layout = QHBoxLayout()
        subject_layout.addWidget(QLabel("Subject:"))
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("Email subject")
        subject_layout.addWidget(self.subject_input)
        compose_layout.addLayout(subject_layout)

        # Body
        compose_layout.addWidget(QLabel("Email Body:"))
        self.body_input = QTextEdit()
        self.body_input.setPlaceholderText(
            "Your email content here...\n\n"
            "Note: 'Dear {first_name} {last_name},' will be automatically added at the beginning.\n\n"
            "You can also use these variables in your text: {email}, {first_name}, {last_name}"
        )
        compose_layout.addWidget(self.body_input)

        compose_group.setLayout(compose_layout)
        email_layout.addWidget(compose_group)

        # Send section
        send_layout = QHBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        send_layout.addWidget(self.progress_bar)

        self.send_btn = QPushButton("Send Emails")
        self.send_btn.clicked.connect(self.send_emails)
        self.send_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; padding: 10px; font-weight: bold; }"
        )
        send_layout.addWidget(self.send_btn)

        email_layout.addLayout(send_layout)

        email_tab.setLayout(email_layout)
        tabs.addTab(email_tab, "Compose Email")

        # Settings tab
        self.settings_widget = SettingsWidget()
        tabs.addTab(self.settings_widget, "Settings")

        main_layout.addWidget(tabs)

    def browse_csv(self):
        """Open file dialog to select CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            self.load_csv(file_path)

    def load_csv(self, file_path):
        """Load and parse CSV file"""
        try:
            self.recipients = load_csv(file_path)

            if not self.recipients:
                QMessageBox.warning(
                    self, "Warning", "No valid recipients found in CSV file."
                )
                return

            # Update UI
            self.csv_label.setText(Path(file_path).name)
            self.recipients_count_label.setText(
                f"Loaded {len(self.recipients)} recipients"
            )

            # Update table preview
            self.recipients_table.setRowCount(min(5, len(self.recipients)))
            for i, recipient in enumerate(self.recipients[:5]):
                self.recipients_table.setItem(
                    i, 0, QTableWidgetItem(recipient["email"])
                )
                self.recipients_table.setItem(
                    i, 1, QTableWidgetItem(recipient["first_name"])
                )
                self.recipients_table.setItem(
                    i, 2, QTableWidgetItem(recipient["last_name"])
                )

            self.recipients_table.resizeColumnsToContents()

            QMessageBox.information(
                self,
                "Success",
                f"Successfully loaded {len(self.recipients)} recipients!\n\n"
                f"Required columns found: email, first_name, last_name",
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load CSV: {str(e)}")

    def send_emails(self):
        """Validate and send emails"""
        # Validation
        if not self.recipients:
            QMessageBox.warning(self, "Warning", "Please upload a CSV file first.")
            return

        if not self.subject_input.text().strip():
            QMessageBox.warning(self, "Warning", "Please enter an email subject.")
            return

        if not self.body_input.toPlainText().strip():
            QMessageBox.warning(self, "Warning", "Please enter email body.")
            return

        settings = self.settings_widget.get_settings()

        # Validate settings
        is_valid, error_msg = validate_email_settings(settings)
        if not is_valid:
            QMessageBox.warning(
                self,
                "Settings Required",
                f"{error_msg}\n\nPlease configure your email settings in the Settings tab.",
            )
            return

        # Confirm send
        reply = QMessageBox.question(
            self,
            "Confirm Send",
            f"Send email to {len(self.recipients)} recipients?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.No:
            return

        # Start sending
        self.send_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(self.recipients))

        # Create and start thread
        self.email_thread = EmailThread(
            self.recipients,
            self.subject_input.text(),
            self.body_input.toPlainText(),
            settings,
        )
        self.email_thread.progress.connect(self.update_progress)
        self.email_thread.finished.connect(self.sending_finished)
        self.email_thread.start()

    def update_progress(self, current, total, message):
        """Update progress bar"""
        self.progress_bar.setValue(current)
        self.statusBar().showMessage(message)

    def sending_finished(self, success, message):
        """Handle sending completion"""
        self.send_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.statusBar().clearMessage()

        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
