# cisco-backup

# Cisco Device Backup Script

This script is designed to back up the configuration of Cisco devices (using SSH or Telnet) and optionally copy the backups to a remote server. It reads device details from a CSV file, connects to each device, retrieves the running configuration, and stores it locally. Optionally, the backups can be transferred to a remote server.

## Features

- **Device Backup**: Retrieves the running configuration from Cisco devices.
- **Local Storage**: Saves backups locally in a directory named after the current date.
- **Remote Storage**: Optionally copies the backup files to a remote server using network shares.
- **Logging**: Logs all activities and errors to a daily log file.

### Installation

1. **Clone the Repository**:

   ```sh
   git clone https://github.com/farshidmousavii/network-backup
   cd network-backup
   ```

2. **Install Dependencies**:
   You can install the required Python packages using the requirements.txt file:
   ```sh
    pip install -r requirements.txt
   ```

## Environment Variables

If using the remote copy feature, the following environment variables must be set in a .env file:

    BACKUP_HOST: The hostname or IP address of the remote server.
    BACKUP_PATH: The directory path on the remote server where backups will be stored.
    USER: The username for accessing the remote server.
    PASSWORD: The password for accessing the remote server.

format of remote host must be like this :

    BACKUP_HOST=backup-server
    BACKUP_PATH=folder1\\folder2\\folder3

use \\\ instead of \

## Usage

Command-Line Arguments

    -c, --csv: (Required) The CSV file containing device information.
    -r, --remote: (Optional) Copy the backup files to a remote server.
    -l, --local: (Optional) Perform only a local backup.

## CSV File Format

The CSV file should be formatted as follows:

    ipaddr,username,password,secret,ssh
    10.10.10.10,admin,cisco,cisco_secret,TRUE
    10.10.10.11,admin,cisco,cisco_secret,FALSE

CSV

    ipaddr: The IP address of the device.
    username: The username to log in to the device.
    password: The password to log in to the device.
    secret: The enable password (or secret) for the device.
    ssh: Set to TRUE for SSH connection, or FALSE for Telnet.

## Example Command

To run the script and back up devices listed in NetworkDevices.csv:

Local backup only:

    python main.py --csv NetworkDevices.csv --local
    python main.py --csv NetworkDevices.csv -l

Backup and copy to a remote server:

    python main.py --csv NetworkDevices.csv --remote
    python main.py --csv NetworkDevices.csv -r
