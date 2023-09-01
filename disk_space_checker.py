import paramiko
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class DiskSpaceChecker:
    def __init__(self, hostname):
        self.hostname = hostname
        self.username = os.getenv("SSH_USERNAME")
        self.password = os.getenv("SSH_PASSWORD")

    def get_disk_space(self):
        try:
            # Create an SSH client
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to the remote host
            ssh_client.connect(self.hostname, username=self.username, password=self.password)

            # Execute the 'df' command to get disk space information
            stdin, stdout, stderr = ssh_client.exec_command('df -h')

            # Read and parse the output
            output = stdout.read().decode('utf-8')

            # Save the disk space information to a text file
            with open(f"{self.hostname}_disk_space.txt", "w") as file:
                file.write(f"Disk space information for {self.hostname}:\n{output}")

            print(f"Disk space information for {self.hostname} written to {self.hostname}_disk_space.txt")

        except Exception as e:
            print(f"An error occurred for {self.hostname}: {e}")

        finally:
            # Close the SSH connection
            ssh_client.close()
