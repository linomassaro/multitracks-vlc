import os
import subprocess
import socket
import time
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, QComboBox,
                             QVBoxLayout, QWidget, QFileDialog, QMessageBox, QSlider, QHBoxLayout)
from PyQt5.QtCore import Qt, QTimer
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
        self.initUI()

    def initUI(self):
        """
        Set up the user interface.
        """
        self.setWindowTitle("Multitracks VLC")
        self.setGeometry(100, 100, 600, 400)
        self.setWindowIcon(QIcon('icon.ico'))

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.video_label = QLabel("No video selected")
        self.layout.addWidget(self.video_label)

        self.select_video_btn = QPushButton("Select Video")
        self.select_video_btn.clicked.connect(self.select_video)
        self.layout.addWidget(self.select_video_btn)

        self.audio_track1_label = QLabel("Select Audio Track 1:")
        self.layout.addWidget(self.audio_track1_label)
        self.audio_dropdown1 = QComboBox()
        self.layout.addWidget(self.audio_dropdown1)

        self.audio_track2_label = QLabel("Select Audio Track 2:")
        self.layout.addWidget(self.audio_track2_label)
        self.audio_dropdown2 = QComboBox()
        self.layout.addWidget(self.audio_dropdown2)

        self.audio_device1_label = QLabel("Select Audio Device 1:")
        self.layout.addWidget(self.audio_device1_label)
        self.audio_devices = self.get_audio_devices()
        self.audio_device_dropdown1 = QComboBox()
        self.audio_device_dropdown1.addItems([dev_name for dev_id, dev_name in self.audio_devices])
        self.layout.addWidget(self.audio_device_dropdown1)

        self.audio_device2_label = QLabel("Select Audio Device 2:")
        self.layout.addWidget(self.audio_device2_label)
        self.audio_device_dropdown2 = QComboBox()
        self.audio_device_dropdown2.addItems([dev_name for dev_id, dev_name in self.audio_devices])
        self.layout.addWidget(self.audio_device_dropdown2)

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

        self.volume_label1 = QLabel("Volume Track 1:")
        self.layout.addWidget(self.volume_label1)
        self.volume_label1.hide()

        self.volume_slider1 = QSlider(Qt.Horizontal)
        self.volume_slider1.setMinimum(0)
        self.volume_slider1.setMaximum(100)
        self.volume_slider1.setValue(100)
        self.volume_slider1.valueChanged.connect(self.update_volume1)
        self.layout.addWidget(self.volume_slider1)
        self.volume_slider1.hide()

        self.volume_label2 = QLabel("Volume Track 2:")
        self.layout.addWidget(self.volume_label2)
        self.volume_label2.hide()

        self.volume_slider2 = QSlider(Qt.Horizontal)
        self.volume_slider2.setMinimum(0)
        self.volume_slider2.setMaximum(100)
        self.volume_slider2.setValue(100)
        self.volume_slider2.valueChanged.connect(self.update_volume2)
        self.layout.addWidget(self.volume_slider2)
        self.volume_slider2.hide()

        self.quit_btn = QPushButton("Quit")
        self.quit_btn.setStyleSheet("background-color: red; color: white;")
        self.quit_btn.clicked.connect(self.quit_app)
        self.layout.addWidget(self.quit_btn)

    def select_video(self):
        """
        Open a file dialog to select a video file and populate audio tracks.
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
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
        audio_track1 = self.audio_dropdown1.currentIndex()
        audio_track2 = self.audio_dropdown2.currentIndex()
        device1 = self.audio_device_dropdown1.currentText()
        device2 = self.audio_device_dropdown2.currentText()

        if not self.video_file or not device1 or not device2:
            QMessageBox.critical(self, "Error", "Please select a video and audio devices.")
            return

        device1_guid = next((dev_id for dev_id, dev_name in self.audio_devices if dev_name == device1), None)
        device2_guid = next((dev_id for dev_id, dev_name in self.audio_devices if dev_name == device2), None)

        if not device1_guid or not device2_guid:
            QMessageBox.critical(self, "Error", "Unable to retrieve GUIDs of the audio devices.")
            return

        try:
            self.start_vlc_instances(self.video_file, audio_track1, audio_track2, device1_guid, device2_guid)
            self.send_command("localhost", 4212, "play")
            self.send_command("localhost", 4213, "play")
            self.show_playback_controls()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def pause(self):
        """
        Pause the video playback.
        """
        self.send_command("localhost", 4212, "pause")
        self.send_command("localhost", 4213, "pause")
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
        self.send_command("localhost", 4212, f"seek {time_position}")
        self.send_command("localhost", 4213, f"seek {time_position}")
        self.time_label.setText(self.format_time(time_position))

    def update_volume1(self, value):
        """
        Update the volume of the first audio track.

        Args:
            value (int): The new volume level.
        """
        self.send_command("localhost", 4212, f"volume {value * 512 // 100}")

    def update_volume2(self, value):
        """
        Update the volume of the second audio track.

        Args:
            value (int): The new volume level.
        """
        self.send_command("localhost", 4213, f"volume {value * 512 // 100}")

    def quit_app(self):
        """
        Quit the application and stop VLC instances.
        """
        self.send_command("localhost", 4212, "quit", is_quit=True)
        self.send_command("localhost", 4213, "quit", is_quit=True)
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
        self.audio_track1_label.hide()
        self.audio_dropdown1.hide()
        self.audio_track2_label.hide()
        self.audio_dropdown2.hide()
        self.audio_device1_label.hide()
        self.audio_device_dropdown1.hide()
        self.audio_device2_label.hide()
        self.audio_device_dropdown2.hide()
        self.start_video_btn.hide()
        self.pause_btn.show()
        self.seek_bar.show()
        self.time_label.show()
        self.volume_label1.show()
        self.volume_slider1.show()
        self.volume_label2.show()
        self.volume_slider2.show()

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

    def start_vlc_instances(self, video_file, audio_track1, audio_track2, device1_guid, device2_guid):
        """
        Start two VLC instances with specified audio tracks and devices.

        Args:
            video_file (str): Path to the video file.
            audio_track1 (int): Index of the first audio track.
            audio_track2 (int): Index of the second audio track.
            device1_guid (str): GUID of the first audio device.
            device2_guid (str): GUID of the second audio device.
        """
        video_file = os.path.abspath(video_file)
        vlc_cmd1 = [
            r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
            video_file,
            f"--audio-track={audio_track1}",
            f"--aout=directx",
            f"--directx-audio-device={device1_guid}",
            "--no-video-title-show",
            "--rc-host=localhost:4212",
            "--extraintf=rc",
            "--intf=dummy",
            "--fullscreen"
        ]
        vlc_cmd2 = [
            r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
            video_file,
            f"--audio-track={audio_track2}",
            f"--aout=directx",
            f"--directx-audio-device={device2_guid}",
            "--no-video-title-show",
            "--rc-host=localhost:4213",
            "--extraintf=rc",
            "--intf=dummy",
            "--novideo"
        ]
        subprocess.Popen(vlc_cmd1, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.Popen(vlc_cmd2, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
        Convert seconds to hh:mm:ss format.

        Args:
            seconds (int): Time in seconds.

        Returns:
            str: Time in hh:mm:ss format.
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
        self.audio_dropdown1.clear()
        self.audio_dropdown2.clear()
        for language_code, language_name in self.audio_tracks:
            icon_path = f"flags/{language_code.split('-')[1].lower()}.svg" if '-' in language_code else f"flags/{language_code.lower()}.svg"
            icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
            self.audio_dropdown1.addItem(icon, language_name)
            self.audio_dropdown2.addItem(icon, language_name)
        self.audio_dropdown1.setCurrentIndex(0)
        self.audio_dropdown2.setCurrentIndex(1 if len(self.audio_tracks) > 1 else 0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MultitracksVLC()
    window.show()
    sys.exit(app.exec_())
