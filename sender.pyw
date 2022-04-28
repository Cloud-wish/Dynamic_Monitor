from urllib import response
import requests
import time
import os
import sys
import json

def send_guild_channel_msg(message):
    response = requests.post("http://127.0.0.1:5700/send_guild_channel_msg", data = message, headers={'Connection':'close'})
    return response

def messageSend():
    message = {
        "guild_id":sys.argv[1],
        "channel_id":sys.argv[2],
        "message":sys.argv[3]
    }
    log_file = sys.argv[4]
    try:
        response = send_guild_channel_msg(message)
        logfile = open(log_file,'a', encoding = 'UTF-8')
        logfile.write(time.strftime('%Y-%m-%d %H:%M:%S\n',time.localtime(time.time())))
        logfile.write(str(response)+' '+response.text+'\n')
        logfile.close()
        return json.loads(response.text)
    except Exception as e:
        logfile = open(log_file,'a', encoding = 'UTF-8')
        logfile.write(time.strftime('%Y-%m-%d %H:%M:%S\n',time.localtime(time.time())))
        logfile.write(repr(e)+'\n')
        logfile.close()
        print(repr(e))
        os._exit(-1)
            
if __name__ == '__main__':
    cnt = 1
    response = messageSend()
    while(cnt < 3 and response['data']['message_id'].startswith('0-')):
        time.sleep(0.03)
        response = messageSend()
        cnt = cnt + 1
