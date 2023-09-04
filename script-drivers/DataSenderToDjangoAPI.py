# DataSenderToDjangoAPI.py

import json
import os

# import requests


class DataSenderToDjangoAPI:
    def __init__(self, root_folder, api_endpoint):
        self.root_folder = root_folder
        self.api_endpoint = api_endpoint

    def create_folder_if_not_exists(self, folder_path):
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    def read_text_file_and_convert_to_json(self, filepath):
        try:
            with open(filepath, "r") as file:
                text_data = file.read()

            # Split the text data into lines
            lines = text_data.strip().split('\n')

            # Extract the header (fields) and data rows (values)
            header = lines[0].split()
            data_rows = [line.split() for line in lines[1:]]

            # Create a dictionary for the parsed data
            parsed_data = {}
            for row in data_rows:
                for i, field in enumerate(header):
                    parsed_data[field] = row[i]

            # Convert the parsed data to a JSON object
            # You can customize the formatting
            json_data = json.dumps(parsed_data, indent=4)

            return json_data

        except Exception as e:
            print(f"An error occurred while processing {filepath}: {e}")
            return None

    def iterate_folders_and_send_to_api(self, ips):
        for ip in ips:
            ip_folder = os.path.join(self.root_folder, ip)

            if not os.path.exists(ip_folder):
                print(f"Folder for IP {ip} not found.")
                continue

            # Find all .txt files in the IP-specific folder
            txt_files = [filename for filename in os.listdir(
                ip_folder) if filename.endswith(".txt")]
            # Sort the list of .txt files by modification time in descending order (latest first)
            txt_files.sort(key=lambda x: os.path.getmtime(
                os.path.join(ip_folder, x)), reverse=True)

            # Get the latest .txt file
            latest_txt_file = txt_files[0]
            filepath = os.path.join(ip_folder, latest_txt_file)
            json_data = self.read_text_file_and_convert_to_json(filepath)

            if json_data:
                # Now you have a JSON object with fields and values from the .txt file for the IP
                print(f"JSON data for IP {ip} from {latest_txt_file}:")
                print(json_data)

            # for txt_file in txt_files:
            #     filepath = os.path.join(ip_folder, txt_file)

            #     json_data = self.read_text_file_and_convert_to_json(filepath)

            #     if json_data:
            #         # Now you have a JSON object with fields and values from the .txt file for the IP
            #         print(f"JSON data for IP {ip} from {txt_file}:")
            #         print(json_data)
