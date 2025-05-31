import os
import time
import subprocess

def monitor_file(file_path, script_path, check_interval=20):
    last_modified_time = os.path.getmtime(file_path)

    while True:
        time.sleep(check_interval)
        current_modified_time = os.path.getmtime(file_path)

        if current_modified_time == last_modified_time:
            print(f"{file_path} has not been updated for {check_interval} seconds. Restarting {script_path}...")
            subprocess.run(["python", script_path])
        else:
            last_modified_time = current_modified_time
            print(f"{file_path} updated at {time.ctime(current_modified_time)}.")

if __name__ == "__main__":
    monitor_file("price.csv", "price.py")
