# DataSenderToDjangoAPI.py
import json
import os

import requests

from file_util import FileUtils

# import requests
# Create an instance of FileUtils
file_util_common = FileUtils()
# Access the folder path
today_folder_path = file_util_common.today_folder_path
API_URL = "http://localhost:8000/api/scripts/network-devices/list/"

print(today_folder_path)
print(API_URL)

class LogSender:
    def __init__(self, ):
        self.root_folder = today_folder_path
        self.api_endpoint = API_URL

    def read_text_file_and_convert_to_json(self, filepath):
        try:
            with open(filepath, "r") as file:
                text_data = file.read()
                lines = text_data.strip().split('\n')
                header = lines[0].split()
                data_rows = [line.split() for line in lines[1:]]
                parsed_data = {}
                for row in data_rows:
                    for i, field in enumerate(header):
                        parsed_data[field] = row[i]

                    return parsed_data

        except Exception as e:
            print(f"An error occurred while processing {filepath}: {e}")
            return None

    def clean_and_parse_log_data(self, log_data):
        try:
            # Remove newline characters from the log_data string
            log_data_cleaned = log_data.replace('\n', '')

            # Parse the cleaned log_data string into a JSON object
            log_data_json = json.loads(log_data_cleaned)

            return log_data_json
        except Exception as e:
            print(f"An error occurred while parsing log_data: {e}")
            return {}

    def send_json_data_to_api(self, ip, json_data):
        try:
            # Define headers for the API request
            headers = {
            "Content-Type": "application/json"
            }

            data = {
            "log_data": json_data,
            "device_ip": ip

            }
            print(data)
        
            json_data_str = json.dumps(data)

            response = requests.post(
            api_url, data=json_data_str, headers=headers)

            # Check the response status code
            if response.status_code == 200:
                print("API request was successful.")
            else:
                print(
                f"API request failed with status code: {response.status_code}")

        except Exception as e:
            print(f"An error occurred while sending the API request: {e}")

    def iterate_folders_and_send_to_api(self, ips):
        for ip in ips:
            ip_folder = os.path.join(self.root_folder, ip)

            if not os.path.exists(ip_folder):
               print(f"Folder for IP {ip} not found.")
            continue

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
                print(f"JSON data for IP {ip} from {latest_txt_file}:")
                # print(json_data)
                self.send_json_data_to_api(ip, json_data)
   