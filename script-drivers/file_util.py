import os
from datetime import datetime


class FileUtils:
    def __init__(self):
        # pass

        # Generate a timestamp with seconds
        timestamp = datetime.now().strftime("%d_%m_%Y_%H-%M-%S")

        # Create the folder with today's date if it doesn't exist
        today_folder = timestamp.split('_')[0:3]  # Extract dd, mm, yyyy
        today_folder = "_".join(today_folder)  # Create folder name as dd_mm_yyyy

        # Get the current working directory as the base directory
        base_directory = os.getcwd()

        # Create the full path for today's folder
        today_folder_path = os.path.join(base_directory, today_folder)

        # Create the full path for today's folder
        self.today_folder_path = self.create_folder_if_not_exists(os.path.join(base_directory, today_folder))

        # # Use the FileUtils method to create the folder if it doesn't exist
        # self.create_folder_if_not_exists(today_folder_path)
    
   
    def get_today_folder_path(self):
        return self.today_folder_path

    @staticmethod
    def create_folder_if_not_exists(folder_path):
        """
        Create a folder if it doesn't exist.

        Args:
            folder_path (str): The path of the folder to create.
        """
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        return folder_path

    @staticmethod
    def read_file(file_path):
        """
        Read the contents of a file.

        Args:
            file_path (str): The path of the file to read.

        Returns:
            str: The contents of the file.
        """
        with open(file_path, 'r') as file:
            return file.read()

    @staticmethod
    def write_file(file_path, content):
        """
        Write content to a file.

        Args:
            file_path (str): The path of the file to write to.
            content (str): The content to write to the file.
        """
        with open(file_path, 'w') as file:
            file.write(content)

    @staticmethod
    def list_files_in_directory(directory):
        """
        List all files in a directory.

        Args:
            directory (str): The path of the directory to list files from.

        Returns:
            list: A list of file names in the directory.
        """
        return os.listdir(directory)

# Example usage:
# file_utils = FileUtils()
# file_utils.create_folder_if_not_exists("my_folder")
# content = file_utils.read_file("my_file.txt")
# file_utils.write_file("new_file.txt", "Hello, World!")
# files = file_utils.list_files_in_directory("my_directory")
