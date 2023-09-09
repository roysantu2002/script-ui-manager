from file_util import FileUtils
import logging
import ast

# Create an instance of FileUtils
file_util_common = FileUtils()

# Access the today_folder_path attribute directly
today_folder_path_0 = file_util_common.today_folder_path
print(today_folder_path_0)

today_folder_path_1 = file_util_common.get_today_folder_path()
print(today_folder_path_1)