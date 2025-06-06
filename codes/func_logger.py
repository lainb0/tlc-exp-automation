import sys
import os
import json
import time
from time import perf_counter
from datetime import datetime

# SDKのモジュールがあるパス（相対パスで設定）
current_dir = os.path.dirname(os.path.abspath(__file__))
sdk_path = os.path.abspath(os.path.join(current_dir, "..", "codes"))
sys.path.append(sdk_path)

# SDKモジュールのimport
from usb import Usb

# タイムアウト設定
Timeout_default = 5

# 以下、get_ch1(), set_time()などはそのままでOK
# 例：get_ch1()
def get_ch1():
    ID = 0
    usb = Usb(Timeout_default)
    command = ":MEAS:OUTP:ONEJSON?"

    for attempt in range(5):
        try:
            if not usb.open(ID):
                print("Connection error")
                time.sleep(1)
                continue

            msgBuf = usb.send_read_command(command, Timeout_default)

            try:
                if isinstance(msgBuf, bytes):
                    msgBuf = msgBuf.decode("utf-8")

                json_data = json.loads(msgBuf)

                for data in json_data["datas"]:
                    if data["name"] == "ch" and data["items"].get("ch") == "1":
                        ch1_temperature = float(data["items"]["value"])
                        usb.close()
                        return ch1_temperature
            except Exception as e:
                print(f"Failed to parse JSON: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            if usb.devio:
                usb.close()

        time.sleep(1)

    print("Failed to fetch CH1 data after 5 attempts")
    return False

def set_time():
    ID = 0
    usb = Usb(Timeout_default)

    for i in range(3):
        try:
            if not usb.open(ID):
                print("Connection error")
                time.sleep(1)
                continue

            now = datetime.now()
            formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
            command = f':OPT:DATE "{formatted_time}"'

            if usb.send_command(command):
                print(f"Date and time set to {formatted_time}")
                return True
            else:
                print("Failed to set date and time")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            if usb.devio:
                usb.close()
        time.sleep(1)

    print("Failed to set date and time after 3 attempts")
    return False


def measure_start():
    ID = 0
    usb = Usb(Timeout_default)

    for attempt in range(3):  # 最大3回試行
        try:
            if not usb.open(ID):
                print("Connection error")
                time.sleep(1)  # 次の試行まで待機
                continue

            command = ":MEAS:START"

            if usb.send_command(command):
                print("Recording started")
                return True  # 成功時にTrueを返す
            else:
                print("Failed to start recording")

        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            if usb.devio:
                usb.close()

        time.sleep(1)  # 次の試行まで待機

    print("Failed to start recording after 3 attempts")
    return False  # 3回失敗した場合にFalseを返す


def measure_stop():
    ID = 0
    usb = Usb(Timeout_default)

    for attempt in range(3):  # 最大3回試行
        try:
            if not usb.open(ID):
                print("Connection error")
                time.sleep(1)  # 次の試行まで待機
                continue

            command = ":MEAS:STOP"

            if usb.send_command(command):
                print("Recording stopped")
                return True  # 成功時にTrueを返す
            else:
                print("Failed to stop recording")

        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            if usb.devio:
                usb.close()

        time.sleep(1)  # 次の試行まで待機

    print("Failed to stop recording after 3 attempts")
    return False  # 3回失敗した場合にFalseを返す


if __name__ == "__main__":
    temp = get_ch1()
    print(temp)