# Ice Masterbox Control Panel

This project is developed for **iCe Smart Home and Office Systems**. It is a software solution that utilizes the MQTT protocol for device control and status monitoring. The software retrieves device information from a CSV file and connects to an MQTT server to manage these devices.

## Features
- **MQTT Protocol**: Provides dynamic communication for devices using the Paho MQTT library.
- **CSV Processing**: Reads device information from a CSV file and subscribes to MQTT topics accordingly.
- **Alarm System**: Can produce an audible alarm when required.
- **Real-Time Device Monitoring**: Tracks device statuses in real time through messages received from the MQTT server.

## Requirements
- Python 3.8 or higher
- `paho-mqtt`
- `customtkinter`
- `sounddevice`
- `numpy`

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/YusufAysu/alanya-control-panel.git
   cd alanya-control-panel
   ```

2. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Add the `Alanya.csv` file to the project directory and define the device information in this file.

## Usage
1. To start the software, run the following command:
   ```bash
   python masterboxController_AlanyaUluPanaroma.py
   ```

2. Upon launching the program:
   - It connects to the MQTT server.
   - Subscribes to MQTT topics based on the devices defined in the `Alanya.csv` file.
   - Provides a GUI for monitoring and controlling devices.

## File Structure
- **masterboxController_AlanyaUluPanaroma.py**: Main application file.
- **Alanya.csv**: File containing device information.

## Example CSV Format
| Apartment | License              | IP              | Status              | Type | Room Number |
|-----------|----------------------|-----------------|---------------------|------|-------------|
| 0.0       | 02.01.65CF32FD.50FC | 192.168.10.10   | Ok - Water Valve    | 1.0  | 1101        |
| 1.0       | 02.02.660D8774.465E | 192.168.10.10   | Ok - Water Valve    | 2.0  | 1101        |

## License
This project is developed by **iCe Smart Home and Office Systems**. All rights reserved.

## Contact
- **Developer**: Yusuf Aysu  
- **Email**: yusuf.aaysu@gmail.com
