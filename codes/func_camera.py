import pypylon.pylon as py
import numpy as np
from PIL import Image
import time
import datetime
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sdk_path = os.path.abspath(os.path.join(current_dir, "..", "codes"))
sys.path.append(sdk_path)


def capture_test(
    OUTPUT_PASS,
    objective_value,
    EXPOSURE_TIME,
    PIXEL_FORMAT,
    CAPTURE_TIME,
    CAMERA_SERIAL_1,
    CAMERA_SERIAL_2,
    CAMERA_NAME_1,
    CAMERA_NAME_2,
):
    if PIXEL_FORMAT != "Mono12":
        print("TIFFに変換する箇所を変更してください")
        return False

    camera_serial_1 = CAMERA_SERIAL_1
    camera_serial_2 = CAMERA_SERIAL_2

    # 出力フォルダの作成
    outputs_folder_camera_1 = (
        f"{OUTPUT_PASS}/{CAMERA_NAME_1}/{int(round(objective_value * 10))}"
    )
    outputs_folder_camera_2 = (
        f"{OUTPUT_PASS}/{CAMERA_NAME_2}/{int(round(objective_value * 10))}"
    )
    os.makedirs(outputs_folder_camera_1, exist_ok=True)
    os.makedirs(outputs_folder_camera_2, exist_ok=True)

    # ファイルが存在しない場合にのみファイルを作成
    if not os.path.exists(f"{OUTPUT_PASS}/capture_time.csv"):
        with open(f"{OUTPUT_PASS}/capture_time.csv", "w") as f:
            f.write("objective_value,capture_time\n")

    # カメラの初期化
    tlf = py.TlFactory.GetInstance()
    devices = tlf.EnumerateDevices()

    if not devices:
        raise RuntimeError("No cameras detected.")

    # カメラの初期化
    target_device_camera_1 = None
    for device in devices:
        if device.GetSerialNumber() == camera_serial_1:
            target_device_camera_1 = device
            break

    if target_device_camera_1 is None:
        raise RuntimeError(
            f"Color camera with serial number {camera_serial_1} not found."
        )

    camera_1 = py.InstantCamera(tlf.CreateDevice(target_device_camera_1))

    # モノクロカメラの初期化
    target_device_camera_2 = None
    for device in devices:
        if device.GetSerialNumber() == camera_serial_2:
            target_device_camera_2 = device
            break

    if target_device_camera_2 is None:
        raise RuntimeError(
            f"Mono camera with serial number {camera_serial_2} not found."
        )

    camera_2 = py.InstantCamera(tlf.CreateDevice(target_device_camera_2))

    try:
        camera_1.Open()
        print(f"Connected to CAMERA 1 with serial number: {camera_serial_1}")

        camera_2.Open()
        print(f"Connected to CAMERA 2 with serial number: {camera_serial_2}")

        camera_1.MaxNumBuffer = 500  # カメラのバッファを設定
        camera_2.MaxNumBuffer = 500  # カメラのバッファを設定

        camera_1.GetNodeMap().GetNode(
            "PixelFormat"
        ).Value = PIXEL_FORMAT  # カメラ1のフォーマットを設定
        camera_1.ExposureAuto.SetValue("Off")  # オート露光をオフに設定
        camera_1.ExposureMode.SetValue("Timed")  # 露光モードを設定
        camera_1.ExposureTime.SetValue(EXPOSURE_TIME)  # 露光時間を設定
        camera_1.GainAuto.SetValue("Off")  # オートゲインをオフに設定
        camera_1.Gain.SetValue(0)  # ゲインを最小に設定
        camera_1.Gamma.SetValue(1.0)  # ガンマ補正を無効に設定

        camera_2.GetNodeMap().GetNode(
            "PixelFormat"
        ).Value = PIXEL_FORMAT  # カメラ2のフォーマットを設定
        camera_2.ExposureAuto.SetValue("Off")  # オート露光をオフに設定
        camera_2.ExposureMode.SetValue("Timed")  # 露光モードを設定
        camera_2.ExposureTime.SetValue(EXPOSURE_TIME)  # 露光時間を設定
        camera_2.GainAuto.SetValue("Off")  # オートゲインをオフに設定
        camera_2.Gain.SetValue(0)  # ゲインを最小に設定
        camera_2.Gamma.SetValue(1.0)  # ガンマ補正を無効に設定

        camera_1.AcquisitionFrameRateEnable.SetValue(True)
        camera_2.AcquisitionFrameRateEnable.SetValue(True)
        camera_1.AcquisitionFrameRate.SetValue(1_000_000 / EXPOSURE_TIME)
        camera_2.AcquisitionFrameRate.SetValue(1_000_000 / EXPOSURE_TIME)

        image_buffer_camera_1 = []
        image_buffer_camera_2 = []

        # # カメラのバッファをクリア
        # clear_camera_buffer(camera_1)
        # clear_camera_buffer(camera_2)

        # 撮影を開始
        camera_1.StartGrabbing(py.GrabStrategy_LatestImageOnly)
        camera_2.StartGrabbing(py.GrabStrategy_LatestImageOnly)

        start_time = time.time()

        while time.time() - start_time < CAPTURE_TIME:  # 3秒間のループ
            with camera_1.RetrieveResult(5000) as result_camera_1, camera_2.RetrieveResult(5000) as result_camera_2:
                if result_camera_1.GrabSucceeded() and result_camera_2.GrabSucceeded():
                    # 画像データを取得し、バッファに追加
                    img_array_camera_1 = result_camera_1.GetArray()
                    img_array_camera_2 = result_camera_2.GetArray()
                    image_buffer_camera_1.append(img_array_camera_1)
                    image_buffer_camera_2.append(img_array_camera_2)
                else:
                    print("Failed to grab an image!")

        camera_1.StopGrabbing()
        camera_2.StopGrabbing() # 追加

        # 撮影時刻をcsvに記録
        captured_time = datetime.datetime.fromtimestamp(start_time)
        captured_time = captured_time.strftime("%Y-%m-%d_%H-%M-%S")
        write_capture_time(OUTPUT_PASS, objective_value, captured_time)

        # カメラ1の画像を保存
        print(
            f"Captured {len(image_buffer_camera_1)} frames from CAMERA 1. Saving images..."
        )

        for idx, img_array in enumerate(image_buffer_camera_1):
            img_scaled = (img_array * (65535 / 4095)).astype(np.uint16)
            save_path = f"{outputs_folder_camera_1}/{idx}.tiff"
            img_pil = Image.fromarray(img_scaled)
            img_pil.save(save_path)
            print(f"CAMERA 1 image saved at {save_path}")

        # カメラ2の画像を保存
        print(
            f"Captured {len(image_buffer_camera_2)} frames from CAMERA 2. Saving images..."
        )

        for idx, img_array in enumerate(image_buffer_camera_2):
            img_scaled = (img_array * (65535 / 4095)).astype(np.uint16)
            save_path = f"{outputs_folder_camera_2}/{idx}.tiff"
            img_pil = Image.fromarray(img_scaled)
            img_pil.save(save_path)
            print(f"CAMERA 2 image saved at {save_path}")

        end_saving = time.time()
        print(f"Saving completed in {end_saving - start_time:.3f} seconds")
        return True

    except Exception as e:
        print(f"An error occurred: {e}")
        return False

    finally:
        # 必ずカメラを閉じる
        if camera_1.IsOpen():
            camera_1.Close()
        if camera_2.IsOpen():
            camera_2.Close()
        print("Camera closed.")

# カメラのバッファをリセット
def clear_camera_buffer(camera):
    camera.StartGrabbing(py.GrabStrategy_LatestImageOnly)
    while camera.IsGrabbing():
        grab_result = camera.RetrieveResult(0, py.TimeoutHandling_Return)
        if grab_result.GrabSucceeded():
            grab_result.Release()
        else:
            break
    camera.StopGrabbing()


def write_capture_time(OUTPUT_PASS, objective_value, capture_time):
    with open(f"{OUTPUT_PASS}/capture_time.csv", "a") as f:
        f.write(f"{objective_value},{capture_time}\n")
    return


if __name__ == "__main__":
    OUTPUT_PASS = "C:/researches/results/test"
    objective_value = 3
    EXPOSURE_TIME = 10000
    CAPTURE_TIME = 3
    PIXEL_FORMAT = "Mono12"
    CAMERA_SERIAL_1 = "40484804"
    CAMERA_SERIAL_2 = "40524443"
    CAMERA_NAME_1 = "CAMERA_1"
    CAMERA_NAME_2 = "CAMERA_2"

    capture_test(
        OUTPUT_PASS,
        objective_value,
        EXPOSURE_TIME,
        PIXEL_FORMAT,
        CAPTURE_TIME,
        CAMERA_SERIAL_1,
        CAMERA_SERIAL_2,
        CAMERA_NAME_1,
        CAMERA_NAME_2,
    )
