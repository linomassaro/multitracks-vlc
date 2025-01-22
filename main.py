import os
import subprocess
import socket
import time
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, QComboBox,
                             QVBoxLayout, QWidget, QFileDialog, QMessageBox, QSlider, QHBoxLayout,
                             QAction, QToolBar, QDialog, QLineEdit, QGridLayout, QFrame, QSpinBox)
from PyQt5.QtCore import Qt, QTimer, QSettings
from PyQt5.QtGui import QIcon
from pymediainfo import MediaInfo
import ctypes
from ctypes import POINTER, WINFUNCTYPE, c_bool, c_byte, c_char_p

class MultitracksVLC(QMainWindow):
    def __init__(self):
        """
        Initialize the main window and set up the UI.
        """
        super().__init__()
        self.video_file = None
        self.audio_tracks = []
        self.video_duration = 0
        self.vlc_path = r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
        self.num_tracks = 2
        self.video_started = False
        self.timer = QTimer(self)  
        self.timer.timeout.connect(self.update_playback_time)
        self.initUI()

    def initUI(self):
        """
        Set up the user interface.
        """
        self.setWindowTitle("Multitracks VLC")
        self.setGeometry(100, 100, 800, 400)
        self.setWindowIcon(QIcon('icon.ico'))

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.video_label = QLabel("No video selected")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.video_label)

        self.select_video_btn = QPushButton("Select Video")
        self.select_video_btn.clicked.connect(self.select_video)
        self.layout.addWidget(self.select_video_btn)

        self.layout.addWidget(self.create_separation_line())

        self.audio_layouts = []
        self.audio_dropdowns = []
        self.audio_device_dropdowns = []
        self.volume_sliders = []
        self.volume_labels = []

        self.create_audio_layouts()

        self.layout.addWidget(self.create_separation_line())

        self.start_video_btn = QPushButton("Start Video")
        self.start_video_btn.clicked.connect(self.start_video)
        self.layout.addWidget(self.start_video_btn)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause)
        self.layout.addWidget(self.pause_btn)
        self.pause_btn.hide()

        self.seek_bar = QSlider(Qt.Horizontal)
        self.seek_bar.setMinimum(0)
        self.seek_bar.setMaximum(100)
        self.seek_bar.valueChanged.connect(self.update_seek_bar)
        self.layout.addWidget(self.seek_bar)
        self.seek_bar.hide()

        self.time_label = QLabel("00:00:00")
        self.layout.addWidget(self.time_label)
        self.time_label.hide()

        self.layout.addWidget(self.create_separation_line())

        self.quit_btn = QPushButton("Quit")
        self.quit_btn.setStyleSheet("background-color: red; color: white;")
        self.quit_btn.clicked.connect(self.quit_app)
        self.layout.addWidget(self.quit_btn)

        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        self.toolbar.addAction(settings_action)

    def create_vertical_separation_line(self):
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #c5c3c2;")
        return line

    def create_separation_line(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #c5c3c2;")
        return line

    def open_settings(self):
        """
        Open the settings dialog to change the VLC path and number of tracks.
        """
        settings_dialog = SettingsDialog(self.vlc_path, self.num_tracks, self)
        if settings_dialog.exec_() == QDialog.Accepted:
            self.vlc_path = settings_dialog.get_vlc_path()
            self.num_tracks = settings_dialog.get_num_tracks()
            self.update_audio_layouts()

    def select_video(self):
        """
        Open a file dialog to select a video file and populate audio tracks.
        """
        options = QFileDialog.Options()
        self.video_file, _ = QFileDialog.getOpenFileName(self, "Select Video File", "",
                                                         "Video Files (*.mp4 *.mkv *.avi *.mov);;All Files (*)",
                                                         options=options)
        if self.video_file:
            self.video_label.setText(f"Selected Video: {os.path.basename(self.video_file)}")
            self.audio_tracks = self.get_audio_tracks(self.video_file)
            if self.audio_tracks:
                self.populate_audio_dropdowns()
            else:
                QMessageBox.critical(self, "Error", "No audio tracks detected in the selected file.")

            self.video_duration = self.get_video_duration(self.video_file)
            self.seek_bar.setMaximum(self.video_duration)

    def start_video(self):
        """
        Start the video with the selected audio tracks and devices.
        """
        audio_tracks = [dropdown.currentIndex() for dropdown in self.audio_dropdowns]
        devices = [dropdown.currentText() for dropdown in self.audio_device_dropdowns]

        if not self.video_file or any(not device for device in devices):
            QMessageBox.critical(self, "Error", "Please select a video and audio devices.")
            return

        device_guids = [next((dev_id for dev_id, dev_name in self.audio_devices if dev_name == device), None) for device in devices]

        if any(not guid for guid in device_guids):
            QMessageBox.critical(self, "Error", "Unable to retrieve GUIDs of the audio devices.")
            return

        try:
            self.start_vlc_instances(self.video_file, audio_tracks, device_guids)
            for port in range(4212, 4212 + self.num_tracks):
                self.send_command("localhost", port, "play")
            self.show_playback_controls()
            self.video_started = True
            self.timer.start(1000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def update_playback_time(self):
        """Update the seek bar and time label with the current playback time."""
        if not self.video_started:
            return
        current_time = self.get_current_time("localhost", 4212)  # Query first instance
        if current_time is not None:
            # Block signals to prevent triggering seek command
            self.seek_bar.blockSignals(True)
            self.seek_bar.setValue(current_time)
            self.seek_bar.blockSignals(False)
            self.time_label.setText(self.format_time(current_time))

    def get_current_time(self, host, port):
        """Get current playback time with socket timeout."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)  # Prevent blocking the UI
                s.connect((host, port))
                s.sendall(b"get_time\n")
                s.settimeout(0.5)
                response = s.recv(1024).decode().strip()
                if response.isdigit():
                    return int(response)
        except Exception as e:
            print(f"Error getting time: {e}")
        return None

    def pause(self):
        """
        Pause the video playback.
        """
        for port in range(4212, 4212 + self.num_tracks):
            self.send_command("localhost", port, "pause")
        current_time = self.get_current_time("localhost", 4212)
        if current_time is not None:
            self.seek_bar.setValue(current_time)
            self.time_label.setText(self.format_time(current_time))

    def update_seek_bar(self, value):
        """
        Update the seek bar position and synchronize video playback.

        Args:
            value (int): The new position of the seek bar.
        """
        time_position = int(value)
        for port in range(4212, 4212 + self.num_tracks):
            self.send_command("localhost", port, f"seek {time_position}")
        self.time_label.setText(self.format_time(time_position))

    def update_volume(self, index, value):
        """
        Update the volume of the specified audio track.

        Args:
            index (int): The index of the audio track.
            value (int): The new volume level.
        """
        self.send_command("localhost", 4212 + index, f"volume {value * 512 // 100}")

    def quit_app(self):
        """
        Quit the application and stop VLC instances.
        """
        if self.video_started:
            self.timer.stop() 
            for port in range(4212, 4212 + self.num_tracks):
                self.send_command("localhost", port, "quit", is_quit=True)
        QApplication.quit()

    def closeEvent(self, event):
        """
        Handle the window close event.

        Args:
            event (QCloseEvent): The close event.
        """
        self.quit_app()
        event.accept()

    def show_playback_controls(self):
        """
        Show the playback controls and hide the selection controls.
        """
        self.select_video_btn.hide()
        for dropdown in self.audio_dropdowns:
            dropdown.hide()
        for dropdown in self.audio_device_dropdowns:
            dropdown.hide()
        self.start_video_btn.hide()
        self.pause_btn.show()
        self.seek_bar.show()
        self.time_label.show()

        # Create a new layout for the playback controls
        playback_controls_layout = QHBoxLayout()

        for i in range(self.num_tracks):
            track_info_layout = QVBoxLayout()

            # Get the selected audio track and device
            audio_track_index = self.audio_dropdowns[i].currentIndex()
            audio_device_index = self.audio_device_dropdowns[i].currentIndex()
            audio_track_name = self.audio_dropdowns[i].currentText()
            audio_device_name = self.audio_device_dropdowns[i].currentText()

            # Get the language code for the flag
            language_code = self.audio_tracks[audio_track_index][0]
            icon_path = f"flags/{language_code.split('-')[1].lower()}.svg" if '-' in language_code else f"flags/{language_code.lower()}.svg"
            icon = QIcon(icon_path) if os.path.exists(icon_path) else None

            # Create a horizontal layout for the flag and track name
            flag_track_layout = QHBoxLayout()
            if icon:
                flag_label = QLabel()
                flag_label.setPixmap(icon.pixmap(24, 24))
                flag_track_layout.addWidget(flag_label)
            track_name_label = QLabel(audio_track_name)
            flag_track_layout.addWidget(track_name_label)
            flag_track_layout.addStretch()  

            # Create a vertical layout for the volume control and device name
            volume_device_layout = QVBoxLayout()
            volume_layout = QHBoxLayout()
            volume_label = QLabel(f"Volume Track {i + 1}:")
            volume_slider = QSlider(Qt.Horizontal)
            volume_slider.setMinimum(0)
            volume_slider.setMaximum(100)
            volume_slider.setValue(100)
            volume_slider.valueChanged.connect(lambda value, index=i: self.update_volume(index, value))
            volume_layout.addWidget(volume_label)
            volume_layout.addWidget(volume_slider)
            volume_device_layout.addLayout(volume_layout)
            device_name_label = QLabel(audio_device_name)
            volume_device_layout.addWidget(device_name_label)

            # Add the flag_track_layout and volume_device_layout to the track_info_layout
            track_info_layout.addLayout(flag_track_layout)
            track_info_layout.addLayout(volume_device_layout)

            # Add the track info layout to the playback controls layout
            playback_controls_layout.addLayout(track_info_layout)

            if i < self.num_tracks - 1:
                playback_controls_layout.addWidget(self.create_vertical_separation_line())

        # Insert the playback controls layout into the main layout
        self.layout.insertLayout(3, playback_controls_layout)
        self.adjustSize()

        # Hide the audio track and device labels
        for layout in self.audio_layouts:
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item.widget() and isinstance(item.widget(), QLabel):
                    item.widget().hide()

    def get_audio_tracks(self, video_file):
        """
        Retrieve audio tracks from the video file.

        Args:
            video_file (str): Path to the video file.

        Returns:
            list: List of tuples containing language code and description.
        """
        media_info = MediaInfo.parse(video_file)
        audio_tracks = []
        for track in media_info.tracks:
            if track.track_type == "Audio":
                language_code = track.language or "unknown"
                language_name = track.language or f"Track {track.track_id}"
                audio_tracks.append((language_code, language_name))
        return audio_tracks

    def get_audio_devices(self):
        """
        Retrieve audio devices from the system with their DirectSound GUIDs.

        Returns:
            list: List of tuples containing GUID and device description.
        """
        devices = []
        dsound = ctypes.windll.dsound
        GUID = c_byte * 16
        LPDSENUMCALLBACK = WINFUNCTYPE(c_bool, POINTER(GUID), c_char_p, c_char_p)

        def audio_enum_callback(lp_guid, description, module):
            try:
                if lp_guid:
                    guid = bytes(ctypes.cast(lp_guid, POINTER(GUID)).contents)
                    guid_str = f'{{{guid[3]:02X}{guid[2]:02X}{guid[1]:02X}{guid[0]:02X}-' \
                               f'{guid[5]:02X}{guid[4]:02X}-' \
                               f'{guid[7]:02X}{guid[6]:02X}-' \
                               f'{guid[8]:02X}{guid[9]:02X}-' \
                               f'{guid[10]:02X}{guid[11]:02X}{guid[12]:02X}{guid[13]:02X}{guid[14]:02X}{guid[15]:02X}}}'
                    devices.append((guid_str, description.decode('mbcs')))
                else:
                    devices.append((None, description.decode('mbcs')))
            except UnicodeDecodeError:
                devices.append((None, "Unknown Device (Decode Error)"))
            return True

        dsound.DirectSoundEnumerateA(LPDSENUMCALLBACK(audio_enum_callback), None)
        return [device for device in devices if device[0]]

    def start_vlc_instances(self, video_file, audio_tracks, device_guids):
        """
        Start multiple VLC instances with specified audio tracks and devices.

        Args:
            video_file (str): Path to the video file.
            audio_tracks (list): List of indices of the audio tracks.
            device_guids (list): List of GUIDs of the audio devices.
        """
        video_file = os.path.abspath(video_file)
        for i, (audio_track, device_guid) in enumerate(zip(audio_tracks, device_guids)):
            vlc_cmd = [
                self.vlc_path,
                video_file,
                f"--audio-track={audio_track}",
                f"--aout=directx",
                f"--directx-audio-device={device_guid}",
                "--no-video-title-show",
                f"--rc-host=localhost:{4212 + i}",
                "--extraintf=rc",
                "--intf=dummy",
                "--fullscreen" if i == 0 else "--novideo"
            ]
            subprocess.Popen(vlc_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)

    def send_command(self, host, port, command, is_quit=False):
        """
        Send a command via VLC RC interface.

        Args:
            host (str): Host address.
            port (int): Port number.
            command (str): Command to send.
            is_quit (bool): Whether the command is part of the quit process.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
                s.sendall(f"{command}\n".encode())
                time.sleep(0.1)
        except ConnectionRefusedError:
            if not is_quit:
                QMessageBox.critical(None, "Error", f"Unable to connect to {host}:{port}")

    def get_current_time(self, host, port):
        """
        Get the current playback time from VLC.

        Args:
            host (str): Host address.
            port (int): Port number.

        Returns:
            int: Current playback time in seconds, or None if failed.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
                s.sendall(b"get_time\n")
                time.sleep(0.1)
                response = s.recv(1024).decode().strip()
                if response.isdigit():
                    return int(response)
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Unable to get current time: {e}")
        return None

    def format_time(self, seconds):
        """
        Convert seconds to hh\:mm\:ss format.

        Args:
            seconds (int): Time in seconds.

        Returns:
            str: Time in hh\:mm\:ss format.
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def get_video_duration(self, video_file):
        """
        Get the duration of the video file.

        Args:
            video_file (str): Path to the video file.

        Returns:
            int: Duration of the video in seconds.
        """
        media_info = MediaInfo.parse(video_file)
        for track in media_info.tracks:
            if track.track_type == "General":
                return int(track.duration / 1000)
        return 0

    def populate_audio_dropdowns(self):
        """
        Populate the audio track dropdowns with available audio tracks.
        """
        for i, dropdown in enumerate(self.audio_dropdowns):
            dropdown.clear()
            for language_code, language_name in self.audio_tracks:
                icon_path = f"flags/{language_code.split('-')[1].lower()}.svg" if '-' in language_code else f"flags/{language_code.lower()}.svg"
                icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
                dropdown.addItem(icon, language_name)
            if i < len(self.audio_tracks):
                dropdown.setCurrentIndex(i)


    def create_audio_layouts(self):
        """
        Create the audio layouts for the specified number of tracks.
        """
        for i in range(self.num_tracks):
            audio_layout = QVBoxLayout()
            audio_track_label = QLabel(f"Select Audio Track {i + 1}:")
            audio_layout.addWidget(audio_track_label)
            audio_dropdown = QComboBox()
            audio_layout.addWidget(audio_dropdown)

            audio_device_label = QLabel(f"Select Audio Device {i + 1}:")
            audio_layout.addWidget(audio_device_label)
            audio_device_dropdown = QComboBox()
            self.audio_devices = self.get_audio_devices()
            audio_device_dropdown.addItems([dev_name for dev_id, dev_name in self.audio_devices])
            audio_layout.addWidget(audio_device_dropdown)

            volume_layout = QHBoxLayout()
            volume_label = QLabel(f"Volume Track {i + 1}:")
            volume_layout.addWidget(volume_label)
            volume_slider = QSlider(Qt.Horizontal)
            volume_slider.setMinimum(0)
            volume_slider.setMaximum(100)
            volume_slider.setValue(100)
            volume_slider.valueChanged.connect(lambda value, index=i: self.update_volume(index, value))
            volume_layout.addWidget(volume_slider)
            volume_label.hide()
            volume_slider.hide()

            self.audio_layouts.append(audio_layout)
            self.audio_dropdowns.append(audio_dropdown)
            self.audio_device_dropdowns.append(audio_device_dropdown)
            self.volume_sliders.append(volume_slider)
            self.volume_labels.append(volume_label)

        self.update_layout()

    def update_audio_layouts(self):
        """
        Update the audio layouts when the number of tracks changes.
        """
        for layout in self.audio_layouts:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

        self.audio_layouts = []
        self.audio_dropdowns = []
        self.audio_device_dropdowns = []
        self.volume_sliders = []
        self.volume_labels = []

        self.create_audio_layouts()

        new_width = self.num_tracks * 400
        self.setFixedWidth(new_width)

    def update_layout(self):
        """
        Update the main layout to accommodate the new audio layouts.
        """
        audio_selection_layout = QHBoxLayout()
        for i, audio_layout in enumerate(self.audio_layouts):
            volume_layout = QHBoxLayout()
            volume_layout.addWidget(self.volume_labels[i])
            volume_layout.addWidget(self.volume_sliders[i])
            audio_selection_layout.addLayout(volume_layout)
            audio_selection_layout.addLayout(audio_layout)
            if i < len(self.audio_layouts) - 1:
                audio_selection_layout.addWidget(self.create_vertical_separation_line())

        self.layout.insertLayout(3, audio_selection_layout)
        self.adjustSize()

    def clear_layout(self, layout):
        """
        Recursively clear the layout.

        Args:
            layout (QLayout): The layout to clear.
        """
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                self.clear_layout(item.layout())

class SettingsDialog(QDialog):
    def __init__(self, vlc_path, num_tracks, parent=None):
        super().__init__(parent)
        self.vlc_path = vlc_path
        self.num_tracks = num_tracks
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Settings")
        self.setGeometry(100, 100, 400, 250)

        layout = QVBoxLayout()

        self.vlc_path_label = QLabel("VLC Path:")
        layout.addWidget(self.vlc_path_label)

        self.vlc_path_input = QLineEdit(self.vlc_path)
        layout.addWidget(self.vlc_path_input)

        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_vlc)
        layout.addWidget(self.browse_btn)

        self.num_tracks_label = QLabel("Number of Audio Tracks:")
        layout.addWidget(self.num_tracks_label)

        self.num_tracks_input = QSpinBox()
        self.num_tracks_input.setMinimum(2)
        self.num_tracks_input.setValue(self.num_tracks)
        layout.addWidget(self.num_tracks_input)

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.accept)
        layout.addWidget(self.save_btn)

        self.setLayout(layout)

    def browse_vlc(self):
        options = QFileDialog.Options()
        vlc_path, _ = QFileDialog.getOpenFileName(self, "Select VLC Executable", "",
                                                  "Executable Files (*.exe);;All Files (*)",
                                                  options=options)
        if vlc_path:
            self.vlc_path_input.setText(vlc_path)

    def get_vlc_path(self):
        return self.vlc_path_input.text()

    def get_num_tracks(self):
        return self.num_tracks_input.value()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MultitracksVLC()
    window.show()
    sys.exit(app.exec_())
