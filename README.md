# tlc-exp-automation

## はじめに

本プログラムは一部GRAPHTECのSDKを利用しています．[こちら](https://graphtec.co.jp/support/sdk/)からSDKを入手した後に，以下ディレクトリを開いてください．

```directory
GL240_840_SDK/Japanese/SampleProgram/GLSample_Python/
```

その後，以下のファイルをcodes以下にコピーしてください．

- usb.py
- devio.py
- DevIoManager.dll
- GtcDevio.dll
- gtcusbr.dll

```directory.md
tlc-exp-automation/
├── codes/
│ ├── usb.py
│ ├── devio.py
│ ├── DevIoManager.dll
│ ├── GtcDevio.dll
│ └── gtcusbr.dll
└── README.md
```

## 必要なライブラリ

``` command
pip install pypylon Pillow slackweb pyserial modbus-tk pythonnet
```

## 想定する実験系

## 動作の説明

簡単なフローチャートは以下の通りです．

![Image](https://github.com/user-attachments/assets/7f5615c1-7ce0-4bb7-91f8-2a7262fcdee6)

## 各プログラムの説明

### src/main.py

コード内でパラメータ等を指定した後に，このコードを実行してください．SLACK_WEBHOOK_URLについてはを参照してください．

### codes/func_camera.py

カメラの制御を行う関数が定義されています．カメラを２台使用してMono12形式で画像を取得することを想定しています．自分の使用状況に応じて変更してください．

### codes/func_logger.py

データロガー

### codes/func_slack_notification.py

slackのWebhook URLを指定して，Slackに通知を送るための関数が定義されています．[このサイト](https://slack.com/services/new/incoming-webhook)からWebhook URLを取得してください． 

### codes/func_tic.py

