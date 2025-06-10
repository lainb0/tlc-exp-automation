import serial
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu
import time

# デバイスの設定
PORT = "COM3"   # テスト用のポート番号 実際の運用ではmain.pyから取得します

# 以下の設定は使用する通信仕様に応じて変更してください
ADDRESS = 2
BAUDRATE = 9600
BYTESIZE = 8
PARITY = "N"
STOPBITS = 2

# テスト用
OBJECTIVE_VALUE = 120


# 現在値を読み取り
def read_temperature_from_E5CC(port_number):

    try:
        control_e5cc = modbus_rtu.RtuMaster(
            serial.Serial(
                port=port_number,
                baudrate=BAUDRATE,
                bytesize=BYTESIZE,
                parity=PARITY,
                stopbits=STOPBITS,
                xonxoff=0,
            )
        )
        control_e5cc.set_timeout(1)  # タイムアウト設定
        control_e5cc.set_verbose(True)  # デバッグ用に詳細出力を有効化
        # アドレス 0x2000 の値を1レジスタ分読み取る
        A1 = control_e5cc.execute(ADDRESS, cst.READ_HOLDING_REGISTERS, 0x2000, 1)
        e5cc_temperature = float(A1[0])/10
        # 値の表示（必要に応じてスケーリング）
        print(f"Temperature: {e5cc_temperature}°C")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # 終了時に通信を閉じる
        if "control_e5cc" in locals():
            control_e5cc.close()
    return e5cc_temperature


# 目標値を書き込み
# 例: 目標値が35.2℃->objective_value=352
def Rewrite_ObjectiveValue(port_number, objective_value):
    try:
        # Modbus RTUマスターの初期化
        control_e5cc = modbus_rtu.RtuMaster(
            serial.Serial(
                port=port_number,
                baudrate=BAUDRATE,  # デバイス仕様に応じて設定
                bytesize=BYTESIZE,
                parity=PARITY,
                stopbits=STOPBITS,
                xonxoff=0,
            )
        )
        control_e5cc.set_timeout(1)  # タイムアウト設定
        control_e5cc.set_verbose(True)  # デバッグ用に詳細出力を有効化

        # 通信書き込みモードに設定
        control_e5cc.execute(
            ADDRESS, cst.WRITE_SINGLE_REGISTER, 0x0000, output_value=0x0001
        )
        control_e5cc.execute(
            ADDRESS, cst.WRITE_SINGLE_REGISTER, 0x0000, output_value=0x0700
        )

        # 目標値の書き込み
        control_e5cc.execute(
            ADDRESS, cst.WRITE_SINGLE_REGISTER, 0x2103, output_value=objective_value
        )

        # ソフトリセット
        control_e5cc.execute(
            ADDRESS, cst.WRITE_SINGLE_REGISTER, 0x0000, output_value=0x0600
        )

    except Exception as e:
        print(f"An error occurred: {e}")
        return False  # エラー発生時にFalseを返す

    finally:
        # 終了時に通信を閉じる
        if "control_e5cc" in locals():
            control_e5cc.close()

    return True  # 正常終了時にTrueを返す


if __name__ == "__main__":
    port_number = PORT
    objective_value = OBJECTIVE_VALUE
    Rewrite_ObjectiveValue(port_number, objective_value)
    time.sleep(4)
    a = read_temperature_from_E5CC(port_number)
    print(a)
    print(type(a))