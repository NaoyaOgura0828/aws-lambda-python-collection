import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import boto3
from botocore.exceptions import ClientError


def lambda_handler(event, context):

    # 送信用メールアドレス
    sender = os.environ['SENDER_EMAIL_ADDRESS']

    # 受信用メールアドレス
    receiver = os.environ['RECEIVER_EMAIL_ADDRESS']

    # ConfigurationSetの指定。
    configuration_set = os.environ['CONFIGURATION_SET_NAME']

    # リージョン
    aws_region = os.environ['AWS_REGION']

    # Eメールの文字エンコーディング。
    charset = os.environ['CHARACTER_ENCODING']

    # S3バケット名
    s3_bucket_name = os.environ['S3_BUCKET_NAME']

    # 添付ファイル名
    attachment_file_name = os.environ['ATTACHMENT_FILE_NAME']

    # 添付ファイルを格納するLambda内のファイルパス。
    attachment_file_path = '/tmp/' + attachment_file_name

    # メールの件名
    subject = '添付メールの実験'

    # HTML以外のメールクライアントを持つ受信者のためのメール本文。
    body_text = '添付メールの実験,\r\n添付ファイルはありますか？'

    # メールのHTML本文
    body_html = """\
    <html>
    <head></head>
    <body>
    <h1>添付メールの実験</h1>
    <p>添付ファイルはありますか？</p>
    </body>
    </html>
    """

    # 新しいSESリソースを作成し、地域を指定する。
    client = boto3.client('ses', region_name=aws_region)

    # multipart/mixedの親コンテナを作成する。
    message = MIMEMultipart('mixed')
    # Add subject, from and to lines.
    message['Subject'] = subject
    message['From'] = sender
    message['To'] = receiver

    # multipart/alternative の子コンテナを作成する。
    message_body = MIMEMultipart('alternative')

    # テキストとHTMLコンテンツをエンコードし、文字エンコーディングを設定する。
    # ASCIIの範囲外の文字を含むメッセージを送信する場合に必要。
    textpart = MIMEText(body_text.encode(charset), 'plain', charset)
    htmlpart = MIMEText(body_html.encode(charset), 'html', charset)

    # テキスト部分とHTML部分を子コンテナに追加する。
    message_body.attach(textpart)
    message_body.attach(htmlpart)

    # 添付ファイルをS3からダウンロードする。
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(s3_bucket_name)
    bucket.download_file(attachment_file_name, attachment_file_path)

    # 添付ファイル部分を定義し、MIMEApplicationを使用してエンコードする。
    attachment_file = MIMEApplication(open(attachment_file_path, 'rb').read())

    # この部分を添付ファイルとして扱うようにメールクライアントに伝えるヘッダを追加。
    # そして、添付ファイルに名前を付ける。
    attachment_file.add_header('Content-Disposition', 'attachment',
                               filename=os.path.basename(attachment_file_path))

    # multipart/alternative の子コンテナを multipart/mixed にアタッチする。
    # 親コンテナにアタッチする。
    message.attach(message_body)

    # 親コンテナに添付ファイルを追加する。
    message.attach(attachment_file)
    if not configuration_set:
        # configuration_set の指定が無い場合
        try:
            # メールを送信する
            response = client.send_raw_email(
                Source=sender,
                Destinations=[
                    receiver
                ],
                RawMessage={
                    'Data': message.as_string(),
                },
            )
        # エラー処理
        except ClientError as error:
            print('メール送信に失敗しました')
            print(error.response['Error']['Message'])
        else:
            print('メール送信成功！！ Message ID:'),
            print(response['ResponseMetadata']['RequestId'])
    else:
        # configuration_set の指定が有る場合
        try:
            # メールを送信する
            response = client.send_raw_email(
                Source=sender,
                Destinations=[
                    receiver
                ],
                RawMessage={
                    'Data': message.as_string(),
                },
                ConfigurationSetName=configuration_set
            )
        # エラー処理
        except ClientError as error:
            print('メール送信に失敗しました')
            print(error.response['Error']['Message'])
        else:
            print('メール送信成功！！ Message ID:'),
            print(response['ResponseMetadata']['RequestId'])
