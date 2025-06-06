import slackweb

def slack_notification(url, message):
    slack = slackweb.Slack(url=url)
    slack.notify(text=message)

if __name__ == '__main__':
    url = ""    # SlackのWebhook URLをここに入力
    message = "テスト"
    slack_notification(url, message)
