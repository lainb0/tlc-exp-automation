import sys
import os
import numpy as np
import time
from datetime import timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
sdk_path = os.path.abspath(os.path.join(current_dir, "..", "codes"))
sys.path.append(sdk_path)

import func_tic as ft
import func_logger as fl
import func_camera as fc
import func_slack_notification as fsn

# ticのポート番号の設定
PORT_NUMBER = "COM3"

# slack webhook URL
SLACK_WEBHOOK_URL=""    # SlackのWebhook URLを設定してください

# 開始温度，終了温度，温度間隔の設定
START_TEMPERATURE = 24.0
FINISH_TEMPERATURE = 25.0
TEMPERATURE_INTERVAL = 1.0
INITIAL_TEMPERATURE = START_TEMPERATURE - 3.0

# check_stable関数用の定数
STABLE_CHECK_TIMES = 10  # 安定判定のためのデータ取得回数
MEAN_BOUNDARY = 0.11  # 目標値との差がこの値以下なら安定と判定
STD_BOUNDARY = 0.125  # 標準偏差がこの値以下なら安定と判定
SLEEP_TIME = 1.01
ERROR_MAX_FUNC_CHECK_STABLE = 600  # check_stable関数のエラー回数上限
ERROR_ALART_FOR_FUNC_CHECK_STABLE = 300  # check_stable関数のエラー回数のアラート
OBJECTIVE_VALUE_DELTA = -1.0  # 目標値とロガーの差分

# カメラの設定
EXPOSURE_TIME = 150000
CAPTURE_TIME = 1
PIXEL_FORMAT = "Mono12"

CAMERA_SERIAL_1 = "40484804"
CAMERA_SERIAL_2 = "40524443"

CAMERA_NAME_1 = "470"
CAMERA_NAME_2 = "460"

# 出力フォルダの設定
OUTPUT_PASS = f"C:/researches/results/test/{CAMERA_NAME_1}-{CAMERA_NAME_2}"
if not os.path.exists(OUTPUT_PASS):
    os.makedirs(OUTPUT_PASS)


# 温度が安定しているかをチェックする関数
def check_stable(objective_value, objective_value_delta):
    # 温度リストの初期化と初期温度を取得
    logger_temperature_list = np.zeros(STABLE_CHECK_TIMES, dtype=float)
    tic_temperature_list = np.zeros(STABLE_CHECK_TIMES, dtype=float)

    # データを取得
    logger_temperature_list[0] = fl.get_ch1()
    if logger_temperature_list[0] == False:
        print("Error: get_ch1 function")
        return False, objective_value_delta

    tic_temperature_list[0] = ft.read_temperature_from_E5CC(PORT_NUMBER)
    if tic_temperature_list[0] == False:
        print("Error: read_temperature_from_E5CC function")
        return False, objective_value_delta

    for i in range(STABLE_CHECK_TIMES - 1):
        time.sleep(SLEEP_TIME)
        logger_temperature_list[i + 1] = fl.get_ch1()
        if logger_temperature_list[i + 1] == False:
            print("Error: get_ch1 function")
            return False, objective_value_delta

        tic_temperature_list[i + 1] = ft.read_temperature_from_E5CC(PORT_NUMBER)
        if tic_temperature_list[i + 1] == False:
            print("Error: read_temperature_from_E5CC function")
            return False, objective_value_delta

    logger_mean = np.mean(logger_temperature_list)
    logger_std = np.std(logger_temperature_list)
    tic_mean = np.mean(tic_temperature_list)
    tic_std = np.std(tic_temperature_list)

    print(
        f"logger_mean: {logger_mean:.3f}, logger_std: {logger_std:.3f}, tic_mean: {tic_mean:.3f}, tic_std: {tic_std:.3f}"
    )

    # エラー回数の初期化
    error_count = 0

    # アラート送信フラグの初期化
    alart_send = 0

    while True:
        if error_count > ERROR_MAX_FUNC_CHECK_STABLE:
            print("Error: エラーの規定回数を超えたためcheck_stableはFalseを返します")
            return False, objective_value_delta

        if error_count > ERROR_ALART_FOR_FUNC_CHECK_STABLE and alart_send == 0:
            message = "定常の制御に失敗している可能性があります．目視確認してください．"
            fsn.slack_notification(SLACK_WEBHOOK_URL, message)
            alart_send = 1    

        # まずロガーの温度が定常になったかをチェック
        if logger_std <= STD_BOUNDARY:
            # ロガーの温度が目標値に近いかをチェック
            if abs(logger_mean - objective_value) <= MEAN_BOUNDARY:
                print("logger temperature is stable")
                return True, objective_value_delta
            # ロガーの温度は定常だが，目標値に近くないため，ticの温度をチェック
            elif (
                abs(tic_mean - objective_value - objective_value_delta) <= MEAN_BOUNDARY
                and tic_std <= STD_BOUNDARY
            ):
                # ロガーの温度が定常と判定された場合，目標値を変更
                objective_value_delta = tic_mean - logger_mean
                new_objective_value = objective_value + objective_value_delta
                # ログファイルに記録
                write_log_temperature_delta(objective_value, logger_mean, tic_mean)

                if not ft.Rewrite_ObjectiveValue(
                    PORT_NUMBER, int(new_objective_value * 10)
                ):
                    print("Error: Rewrite_ObjectiveValue function")
                    error_stop()
                    return False, objective_value_delta
                time.sleep(4)

        # ロガーもしくはticの温度が定常でないため，再度ロガーのデータを取得
        for i in range(STABLE_CHECK_TIMES - 1):
            logger_temperature_list[i] = logger_temperature_list[i + 1]
            tic_temperature_list[i] = tic_temperature_list[i + 1]
        time.sleep(SLEEP_TIME)

        logger_temperature_list[STABLE_CHECK_TIMES - 1] = fl.get_ch1()
        if logger_temperature_list[STABLE_CHECK_TIMES - 1] == False:
            print("Error: get_ch1 function")
            return False, objective_value_delta

        tic_temperature_list[STABLE_CHECK_TIMES - 1] = ft.read_temperature_from_E5CC(
            PORT_NUMBER
        )
        if tic_temperature_list[STABLE_CHECK_TIMES - 1] == False:
            print("Error: read_temperature_from_E5CC function")
            return False, objective_value_delta

        logger_mean = np.mean(logger_temperature_list)
        logger_std = np.std(logger_temperature_list)
        tic_mean = np.mean(tic_temperature_list)
        tic_std = np.std(tic_temperature_list)
        print(
            f"logger_mean: {logger_mean:.3f}, logger_std: {logger_std:.3f}, tic_mean: {tic_mean:.3f}, tic_std: {tic_std:.3f}"
        )
        error_count += 1


def write_log_temperature_delta(objective_value, logger_mean, tic_mean):
    with open(f"{OUTPUT_PASS}/log_temperature_delta.csv", "a") as f:
        f.write(
            f"{objective_value},{logger_mean},{tic_mean},{logger_mean - tic_mean}\n"
        )

# エラー終了時に温度を初期値に戻すことにtryした後にslackに通知を送る
def error_stop():
    message = "!エラーにより計測を中断しました!"
    fsn.slack_notification(SLACK_WEBHOOK_URL, message)
    if not ft.Rewrite_ObjectiveValue(PORT_NUMBER, int((INITIAL_TEMPERATURE)* 10)):
        print("Error: Rewrite_ObjectiveValue function")


def main():
    # 開始時刻の記録
    start_time = time.time()

    # エラー用のログファイルを初期化
    with open(f"{OUTPUT_PASS}/log_temperature_delta.csv", "w") as f:
        f.write("objective_value,logger_mean,tic_mean,delta\n")

    # ロガーの時刻合わせ
    if not fl.set_time():
        print("Error: set_time function")
        error_stop()
        return False

    objective_value_delta = OBJECTIVE_VALUE_DELTA

    for objective_value in np.arange(
        START_TEMPERATURE,
        FINISH_TEMPERATURE + TEMPERATURE_INTERVAL,
        TEMPERATURE_INTERVAL,
    ):
        # これから実行する目標値を表示
        print(f"Objective temperature: {objective_value}℃")
        if not ft.Rewrite_ObjectiveValue(PORT_NUMBER, int(objective_value * 10 + objective_value_delta * 10)):
            print("Error: Rewrite_ObjectiveValue function")
            error_stop()
            return False
        time.sleep(4)
        # 定常チェック
        stable, objective_value_delta = check_stable(
            objective_value, objective_value_delta
        )
        if stable == True:
            if not fl.measure_start():
                print("Error: measure_start function")
                error_stop()
                return False

            # カメラのキャプチャ
            if not fc.capture_test(
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
                print("Error: capture_test function")
                error_stop()
                return False
            if not fl.measure_stop():
                print("Error: measure_stop function")
                error_stop()
                return False
            time.sleep(3)
        else:
            print("Error: 非定常のため計測を終了します．実験環境や定常条件のパラメータを確認してください．")
            error_stop()
            return False

        # 経過時間の表示
        print(f"Elapsed time: {timedelta(seconds=time.time() - start_time)} ")

    # 最後に目標値を初期温度に戻す
    if not ft.Rewrite_ObjectiveValue(PORT_NUMBER, int((INITIAL_TEMPERATURE)* 10)):
        print("Error: Rewrite_ObjectiveValue function")
        error_stop()
        return False

    # 実行時間の表示
    print(f"Execution time: {timedelta(seconds=time.time() - start_time)}")

    # slackに通知を送る
    message = "計測は終了しました"
    fsn.slack_notification(SLACK_WEBHOOK_URL, message)


if __name__ == "__main__":
    main()
