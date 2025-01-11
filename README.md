# Multitracks VLC

Multitracks VLC is a Python application that allows you to play a video file with two different audio tracks on two different audio devices simultaneously. This is useful for scenarios where you need to output different audio tracks to different devices, such as headphones and speakers.

## Features

- Select a video file with multiple audio tracks.
- Choose two different audio tracks to play simultaneously.
- Select two different audio output devices.
- Control playback with pause, seek, and volume adjustment.
- Synchronized playback of video and audio tracks.

## Requirements

- Python 3.x
- PyQt5
- pymediainfo
- VLC Media Player

## Installation

1. **Install Python**: Ensure you have Python 3.x installed on your system. You can download it from [python.org](https://www.python.org/).

2. **Install Dependencies**: Use pip to install the required Python packages.
    ```sh
    pip install PyQt5 pymediainfo
    ```

3. **Install VLC Media Player**: Download and install VLC Media Player from [videolan.org](https://www.videolan.org/). Ensure that the vlc.exe path is the correct one (main.py#310 & main.py#322).

## Usage

1. **Run the Application**:
    ```sh
    python main.py
    ```

2. **Select Video File**: Click the "Select Video" button to choose a video file with multiple audio tracks.

3. **Choose Audio Tracks**: Select the two audio tracks you want to play from the dropdown menus.

4. **Select Audio Devices**: Choose the two audio output devices from the dropdown menus.

5. **Start Video**: Click the "Start Video" button to begin playback.

6. **Control Playback**: Use the pause button, seek bar, and volume sliders to control playback.

## Code Structure

- `main.py`: The main script that contains the application and all the functionality.
- `icon.ico`: The icon file for the application window.
- `flags/`: Directory containing flag icons for different languages (optional).

## Functions and Methods

### `SynchronizedVLCControl` Class

- **`__init__`**: Initialize the main window and set up the UI.
- **`initUI`**: Set up the user interface.
- **`select_video`**: Open a file dialog to select a video file and populate audio tracks.
- **`start_video`**: Start the video with the selected audio tracks and devices.
- **`pause`**: Pause the video playback.
- **`update_seek_bar`**: Update the seek bar position and synchronize video playback.
- **`update_volume1`**: Update the volume of the first audio track.
- **`update_volume2`**: Update the volume of the second audio track.
- **`quit_app`**: Quit the application and stop VLC instances.
- **`closeEvent`**: Handle the window close event.
- **`show_playback_controls`**: Show the playback controls and hide the selection controls.
- **`get_audio_tracks`**: Retrieve audio tracks from the video file.
- **`get_audio_devices`**: Retrieve audio devices from the system with their DirectSound GUIDs.
- **`start_vlc_instances`**: Start two VLC instances with specified audio tracks and devices.
- **`send_command`**: Send a command via VLC RC interface.
- **`get_current_time`**: Get the current playback time from VLC.
- **`format_time`**: Convert seconds to hh:mm:ss format.
- **`get_video_duration`**: Get the duration of the video file.
- **`populate_audio_dropdowns`**: Populate the audio track dropdowns with available audio tracks.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request if you have any suggestions or improvements.

## Acknowledgments

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/intro)
- [pymediainfo](https://pymediainfo.readthedocs.io/)
- [VLC Media Player](https://www.videolan.org/)