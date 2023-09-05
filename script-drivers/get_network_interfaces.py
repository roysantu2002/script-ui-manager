import os
from datetime import datetime
import paramiko
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_folder_if_not_exists(folder_path):
    """
    Create a folder if it doesn't exist.

    Args:
        folder_path (str): The path of the folder to create.
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

class NetworkInterfaceChecker:
    def __init__(self, hostname):
        self.hostname = hostname
        self.username = os.getenv("SSH_USERNAME")
        self.password = os.getenv("SSH_PASSWORD")

    def get_network_interfaces(self):
        try:
            # Create an SSH client
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to the remote host
            ssh_client.connect(
                self.hostname, username=self.username, password=self.password)

            # Get the IP address
            ip_address = ssh_client.get_transport().sock.getpeername()[0]

            # Execute the command to get network interface information
            stdin, stdout, stderr = ssh_client.exec_command('ifconfig')

            # Read and parse the output
            output = stdout.read().decode('utf-8')

            # Generate a timestamp with seconds
            timestamp = datetime.now().strftime("%d_%m_%Y_%H-%M-%S")

            # Create the folder with today's date if it doesn't exist
            today_folder = timestamp.split('_')[0:3]  # Extract dd, mm, yyyy
            today_folder = "_".join(today_folder)  # Create folder name as dd_mm_yyyy
            folder_path = os.path.join(today_folder, ip_address)

            # Use the generic function
            create_folder_if_not_exists(folder_path)

            # Create the filename with the timestamp
            filename = f"{self.hostname}_network_interfaces_{timestamp}.txt"

            # Save the network interface information to the file inside the today_folder
            with open(os.path.join(folder_path, filename), "w") as file:
                file.write(
                    f"Network interface information for {self.hostname}:\n{output}")

            print(
                f"Network interface information for {self.hostname} written to {self.hostname}_network_interfaces.txt")

        except Exception as e:
            print(f"An error occurred for {self.hostname}: {e}")

        finally:
            # Close the SSH connection
            ssh_client.close()
