import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QComboBox, QPushButton, QRadioButton, QButtonGroup,
                            QTextEdit, QSlider, QLineEdit, QGroupBox)
from PyQt6.QtCore import Qt, QTimer
import serial
import serial.tools.list_ports
from enum import Enum, auto

class Status(Enum):
    IDLE = auto()
    WASTE = auto()
    SOLVENT = auto()
    DELAY_SOLVENT = auto()
    DELAY_WASTE = auto()

class DBestaWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Solvent Recycler Control")
        self.setGeometry(100, 100, 800, 600)
        
        # Serial port variables
        self.serial_port = None
        self.serial_connected = False
        self.baudrate = 9600
        self.port_name = ""
        
        # Status variables
        self.status = Status.IDLE
        self.sol_waste = 0.0
        self.del_waste = 0.0
        
        # UI Setup
        self.init_ui()
        
        # Timer for periodic tasks
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_serial)
        self.timer.start(100)  # Check every 100ms

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Serial Port Section
        serial_group = QGroupBox("RS232 Connection")
        serial_layout = QVBoxLayout()
        
        self.port_combo = QComboBox()
        self.refresh_ports()
        serial_layout.addWidget(QLabel("Select Port:"))
        serial_layout.addWidget(self.port_combo)
        
        self.open_btn = QPushButton("Open Connection")
        self.open_btn.clicked.connect(self.open_serial)
        serial_layout.addWidget(self.open_btn)
        
        self.close_btn = QPushButton("Close Connection")
        self.close_btn.setEnabled(False)
        self.close_btn.clicked.connect(self.close_serial)
        serial_layout.addWidget(self.close_btn)
        
        self.status_label = QLabel("Status: Disconnected")
        serial_layout.addWidget(self.status_label)
        
        serial_group.setLayout(serial_layout)
        main_layout.addWidget(serial_group)
        
        # Position Control Section
        pos_group = QGroupBox("Position Control")
        pos_layout = QVBoxLayout()
        
        self.pos_group = QButtonGroup()
        positions = ["Position 1", "Position 2", "Position 3", 
                    "Position 4", "Position 5", "Position 6"]
        
        for i, pos in enumerate(positions):
            radio = QRadioButton(pos)
            radio.setChecked(i == 0)
            self.pos_group.addButton(radio, i+1)
            pos_layout.addWidget(radio)
        
        self.get_pos_btn = QPushButton("Get Current Position")
        self.get_pos_btn.clicked.connect(self.get_current_position)
        pos_layout.addWidget(self.get_pos_btn)
        
        pos_group.setLayout(pos_layout)
        main_layout.addWidget(pos_group)
        
        # Settings Section
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout()
        
        # Solvent/Waste selection
        solvent_layout = QHBoxLayout()
        solvent_layout.addWidget(QLabel("Solvent Position:"))
        self.solvent_combo = QComboBox()
        self.solvent_combo.addItems(["1", "2", "3", "4", "5", "6"])
        solvent_layout.addWidget(self.solvent_combo)
        
        waste_layout = QHBoxLayout()
        waste_layout.addWidget(QLabel("Waste Position:"))
        self.waste_combo = QComboBox()
        self.waste_combo.addItems(["1", "2", "3", "4", "5", "6"])
        waste_layout.addWidget(self.waste_combo)
        
        # Level controls
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("0-Level:"))
        self.level_input = QLineEdit("0.0")
        self.level_input.textChanged.connect(self.update_range_display)
        level_layout.addWidget(self.level_input)
        
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("Range (%):"))
        self.range_input = QLineEdit("10.0")
        self.range_input.textChanged.connect(self.update_range_display)
        range_layout.addWidget(self.range_input)
        
        self.range_display = QLabel("Range: 0.0 .. 0.0")
        
        # Delay control
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Delay (ms):"))
        self.delay_input = QLineEdit("1000")
        delay_layout.addWidget(self.delay_input)
        
        settings_layout.addLayout(solvent_layout)
        settings_layout.addLayout(waste_layout)
        settings_layout.addLayout(level_layout)
        settings_layout.addLayout(range_layout)
        settings_layout.addWidget(self.range_display)
        settings_layout.addLayout(delay_layout)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(port.device)
        if ports:
            self.port_name = ports[0].device

    def open_serial(self):
        port = self.port_combo.currentText()
        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            self.serial_connected = True
            self.status_label.setText(f"Status: Connected to {port}")
            self.open_btn.setEnabled(False)
            self.close_btn.setEnabled(True)
            self.port_combo.setEnabled(False)
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")

    def close_serial(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.serial_connected = False
        self.status_label.setText("Status: Disconnected")
        self.open_btn.setEnabled(True)
        self.close_btn.setEnabled(False)
        self.port_combo.setEnabled(True)

    def send_frame(self, frame):
        if not self.serial_connected or not self.serial_port:
            return
        
        try:
            self.serial_port.write(frame.encode('utf-8'))
            self.status_label.setText(f"Sent: {frame}")
        except Exception as e:
            self.status_label.setText(f"Send error: {str(e)}")

    def get_current_position(self):
        self.send_frame("42,1,90,0,91")

    def set_position(self, pos):
        frame = f"42,1,{pos},0,{pos+1}"
        self.send_frame(frame)

    def update_range_display(self):
        try:
            level = float(self.level_input.text())
            range_pct = float(self.range_input.text())
            lower = level - (level * range_pct / 100)
            upper = level + (level * range_pct / 100)
            self.range_display.setText(f"Range: {lower:.2f} .. {level:.2f} .. {upper:.2f}")
        except ValueError:
            pass

    def check_serial(self):
        if not self.serial_connected or not self.serial_port:
            return
        
        if self.serial_port.in_waiting:
            try:
                data = self.serial_port.read(self.serial_port.in_waiting)
                self.process_serial_data(data)
            except Exception as e:
                self.status_label.setText(f"Read error: {str(e)}")

    def process_serial_data(self, data):
        # Process incoming serial data
        try:
            decoded = data.decode('utf-8')
            self.status_label.setText(f"Received: {decoded}")
            
            # Example: Update position radio buttons based on received data
            if len(decoded) >= 3:
                pos = int(decoded[2])  # Adjust based on your protocol
                if 1 <= pos <= 6:
                    button = self.pos_group.button(pos)
                    if button:
                        button.setChecked(True)
        except UnicodeDecodeError:
            pass

    def set_besta(self, tx, x):
        try:
            level = float(self.level_input.text())
            range_pct = float(self.range_input.text())
            delay = float(self.delay_input.text())
            
            lower = level - (level * range_pct / 100)
            upper = level + (level * range_pct / 100)
            
            if self.status == Status.SOLVENT:
                if not (lower <= x <= upper):
                    self.status = Status.DELAY_SOLVENT
                    self.sol_waste = tx
            elif self.status == Status.DELAY_SOLVENT:
                if (tx - self.sol_waste) > delay:
                    self.status = Status.WASTE
                    self.sol_waste = 0.0
            elif self.status == Status.WASTE:
                if lower <= x <= upper:
                    self.status = Status.DELAY_WASTE
                    self.del_waste = tx
            elif self.status == Status.DELAY_WASTE:
                if (tx - self.del_waste) > delay:
                    self.status = Status.SOLVENT
                    self.del_waste = 0.0
            
            # Set position based on status
            if self.status == Status.WASTE:
                self.set_position(int(self.waste_combo.currentText()))
            elif self.status == Status.SOLVENT:
                self.set_position(int(self.solvent_combo.currentText()))
                
            print(f"{tx} {self.status.name}")
            
        except ValueError:
            pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DBestaWindow()
    window.show()
    sys.exit(app.exec())