from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

#======python的函數庫==========
import tempfile, os
import datetime
#import openai
import time
import traceback

import requests
#======python的函數庫==========

from azure.core.credentials import AzureKeyCredential
from azure.ai.language.questionanswering import QuestionAnsweringClient

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# OPENAI API Key初始化設定
#openai.api_key = os.getenv('OPENAI_API_KEY')

endpoint = os.getenv('END_POINT')
credential = AzureKeyCredential(os.getenv('AZURE_KEY'))
knowledge_base_project = os.getenv('PROJECT')
deployment = 'production'

api_endpoint = os.getenv('COPILOT_ENDPOINT')

#def GPT_response(text):
    # 接收回應
    #response = openai.Completion.create(model="gpt-3.5-turbo-instruct", prompt=text, temperature=0.5, max_tokens=500)
    #print(response)
    # 重組回應
    #answer = response['choices'][0]['text'].replace('。','')
    #return answer

def QA_response(text):
    client = QuestionAnsweringClient(endpoint, credential)
    with client:
        question=text
        output = client.get_answers(
            question = question,
            project_name=knowledge_base_project,
            deployment_name=deployment
        )
    return output.answers[0].answer

def Copilot_response(text):
# Copilot Studio
    


    # Replace with your API key
    #api_key = "your_api_key_here"
    
    # Headers for the request
    headers = {
    #    "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Data to send in the request
    data = {
        "input": text
    }
    
    # Sending a POST request to the API
    response = requests.post(api_endpoint, headers=headers, json=data)
    
    # Checking the response status
    if response.status_code == 200:
        print("Success!")
        print("Response:", response.json())
    else:
        print("Failed to communicate with Copilot Studio API")
        print("Status Code:", response.status_code)
        print("Response:", response.text)

    return output.answers[0].answer

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    if msg[0]=='-':
        try:
            QA_answer = QA_response(msg)
            print(QA_answer)
            if QA_answer!='No good match found in KB':
                line_bot_api.reply_message(event.reply_token, TextSendMessage(QA_answer))
        except:
            print(traceback.format_exc())
            line_bot_api.reply_message(event.reply_token, TextSendMessage('QA Error'))
    elif msg[0]=='!':
        try:
            QA_answer = Copilot_response(msg)
            print(QA_answer)
            if QA_answer!='No good match found in KB':
                line_bot_api.reply_message(event.reply_token, TextSendMessage(QA_answer))
        except:
            print(traceback.format_exc())
            line_bot_api.reply_message(event.reply_token, TextSendMessage('Copilot Error'))

         

@handler.add(PostbackEvent)
def handle_message(event):
    print(event.postback.data)


@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name}歡迎加入')
    line_bot_api.reply_message(event.reply_token, message)
        
        
import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
