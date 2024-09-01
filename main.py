from netmiko import (
    ConnectHandler,
    NetMikoTimeoutException,
    NetMikoAuthenticationException,
)
from datetime import datetime
from decouple import config, UndefinedValueError
import re
import csv
import sys
import os
import shutil
import win32wnet
import logging
import argparse


log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)
log_file = os.path.join(log_folder, f"log-{datetime.today().date()}.txt")


logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename=log_file,
    level=logging.INFO,
)


def convert_file_to_list(file: str) -> list:
    """
    Function to create list of dictionaries from CSV file and convert to list.
    """
    try:
        with open(file, "r") as file:
            reader = csv.DictReader(file)
            devices = []
            for row in reader:
                device = [
                    row["ip"],
                    row["username"],
                    row["password"],
                    row["secret"],
                    row["ssh"],
                ]
                devices.append(device)
            return devices
    except:
        print(
            "\nInvalid header in CSV file. Please modify to the format below: "
            "\nipaddr,username,password,ssh"
            "\n10.10.10.10,admin,cisco,TRUE"
            "\n10.10.10.11,admin,cisco,FALSE\n"
        )
        sys.exit()


def get_backup(ip: str, username: str, password: str, secret: str, ssh: str):
    """
    This function gets a backup of the device.
    """
    device = {
        "device_type": "cisco_ios" if ssh == "TRUE" else "cisco_ios_telnet",
        "host": ip,
        "username": username,
        "password": password,
        "secret": secret,
    }
    try:
        connection = ConnectHandler(**device)
        connection.enable()
        output = connection.send_command("show running-config")

        converted = output.split("\n")[3:]

        backup_config = "\n".join(converted)
        pattern = r"\bhostname\s+(\S+)"
        match = re.search(pattern, backup_config)
        hostname = match.group(1)

        return {hostname: backup_config}
    except (
        NetMikoTimeoutException,
        NetMikoAuthenticationException,
    ) as e:
        logging.error(str(e))

    except Exception as e:
        logging.error(f"can not connect to {ip}")


def write_backup(directory: str, hostname: str, data: str):
    try:
        path = f"{directory}\\{hostname}"
        file_path = os.path.dirname(os.path.abspath(sys.argv[0]))

        with open(f"{file_path}\\{path}", "w") as file:
            file.write(data)
    except:
        logging.error("Can not create backup")


def copy_to_server(src: str, directory: str):
    """
    Copy the backup directory to a remote server.
    """
    print("Copying to server")

    backup_host = config("BACKUP_HOST", default="localhost")
    packup_path = config("BACKUP_PATH")
    user = config("USER")
    password = config("PASSWORD")

    try:
        # Connect to the remote server
        win32wnet.WNetAddConnection2(
            0,
            None,
            f"\\\\{backup_host}",
            None,
            user,
            password,
        )

        destination = (
            f"\\\\{backup_host}\\{packup_path}\\{directory}"
            if packup_path
            else f"\\\\{backup_host}\\{directory}"
        )

        # Copy the backup directory to the remote server
        shutil.copytree(src, destination)
        print(f"Backup copied to: {destination}")

    except Exception as e:
        logging.error("Cannot connect to network share to copy backup")
        logging.error(str(e))

    finally:
        # Disconnect from the network share
        try:
            win32wnet.WNetCancelConnection2(f"\\\\{backup_host}", 0, 0)
        except Exception as e:
            logging.error("Cannot disconnect from network share")
            logging.error(str(e))


def main(args):
    try:
        if args.remote:
            # Enforce required environment variables
            try:
                config("BACKUP_HOST")
                config("USER")
                config("PASSWORD")
            except UndefinedValueError as e:
                logging.error(str(e))
                print(f"Error: {str(e)}")
                print(
                    "\nIf using the '-r' option for remote backup, please ensure "
                    "the 'BACKUP_HOST','BACKUP_PATH','USER', and 'PASSWORD' environment variables are set in the .env file.\n"
                )
                sys.exit(1)
        directory = str(datetime.today().date())
        file_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        path = os.path.join(file_path, directory)
        copy_path = os.path.join(file_path, directory)

        try:
            os.mkdir(path)
        except OSError:
            shutil.rmtree(copy_path)
            os.mkdir(path)

        start_time = datetime.now()

        # CSV file from arguments
        file = args.csv

        # Convert data to list
        data = convert_file_to_list(file)

        for device in data:
            ip = device[0]
            username = device[1]
            password = device[2]
            secret = device[3]
            ssh = device[4]
            backup = get_backup(ip, username, password, secret, ssh)
            if backup:
                hostname, data = backup.popitem()
                if hostname:
                    write_backup(directory, hostname, data)
                    logging.info(f"{hostname} backup is complete!")
                else:
                    logging.error(f"Backup failed for device with IP: {ip}")
            else:
                logging.error(f"Backup failed for device with IP: {ip}")
        if args.remote:
            copy_to_server(copy_path, directory)
            logging.info("Copy completed")
            shutil.rmtree(copy_path)
            logging.info("Remove folder completed")

        logging.info("\nElapsed time: " + str(datetime.now() - start_time))
    except ValueError as e:
        logging.info("Invalid entry. Please ensure all inputs are correct.")
        logging.error(str(e))
        print("Invalid entry. Please ensure all inputs are correct.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Backup Cisco devices and optionally copy to a remote server."
    )
    parser.add_argument(
        "-c", "--csv", required=True, help="CSV file with device information."
    )
    parser.add_argument(
        "-r", "--remote", action="store_true", help="Copy backup to a remote server."
    )
    parser.add_argument(
        "-l", "--local", action="store_true", help="Only perform a local backup."
    )
    args = parser.parse_args()

    if args.remote or args.local:
        main(args)
    else:
        print(
            "\nThis program is designed to back up Cisco devices\n"
            "\nThe program accepts a CSV file and optional switches for remote or local backup.\n"
            "\nThe CSV should be in the format below:\n"
            "\nipaddr,username,password,secret,ssh"
            "\n10.10.10.10,admin,cisco,cisco_secret,TRUE"
            "\n10.10.10.11,admin,cisco,cisco_secret,FALSE\n"
            "\nUsage: python main.py --csv NetworkDevices.csv [--remote] [--local]\n"
            "\nUse --remote for remote copy, --local for local backup only."
        )
        sys.exit()
