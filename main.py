from ast import operator
import asyncio
from datetime import datetime,date,timedelta
import random
from tokenize import Name
import requests
import json,collections,xml
from bs4 import BeautifulSoup
import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import threading
import queue
import os
from time import sleep
import websockets
import platform

from playwright.async_api import async_playwright

from PIL import Image, ImageFont, ImageDraw
import textwrap

import blivedm

PUSHHELP = """
1./添加微博推送
使用方法：@机器人 /添加微博推送 微博UID
2./添加动态推送
使用方法：@机器人 /添加动态推送 B站UID
3./添加直播推送
使用方法：@机器人 /添加直播推送 B站UID
4./删除微博推送
使用方法：@机器人 /删除微博推送 微博UID
5./删除动态推送
使用方法：@机器人 /删除动态推送 B站UID
6./删除直播推送
使用方法：@机器人 /删除直播推送 B站UID
7./查询配置
显示当前子频道的推送配置
"""

# 微软雅黑的字体
path_to_ttf = f'font{os.sep}msyh.ttc'
font = ImageFont.truetype(path_to_ttf, size=16, encoding='unic')
cur_path=os.path.dirname(__file__)
cur_path=os.path.split(os.path.realpath(__file__))[0]
if(cur_path[-1] != os.sep):
    cur_path = cur_path + os.sep
sys_str = platform.system()

BOT_ID = "xxx" # 此处填写字符串格式的BOT ID
ALLOWED_GUILD = ['xxx', 'xxx'] # 此处填写字符串格式的频道ID，代表启用推送功能的频道

wb_cookie = ''
wb_ua = ''

#dict的key和value之间用:分割
#set的各个项之间用,分割
#每项的频道id和子频道id之间用.分割
#dict各个项之间回车分割
def loadConfig():
    try:
        f = open(f"config{os.sep}pushwbConfig.conf","r",encoding="UTF-8")
        pushwbConfigList = f.read().split()
        f.close()
    except:
        os.makedirs("config", exist_ok=True)
        f = open(f"config{os.sep}pushwbConfig.conf","w",encoding="UTF-8")
        f.close()
        pushwbConfigList = []
    try:
        f = open(f"config{os.sep}pushdynConfig.conf","r",encoding="UTF-8")
        pushdynConfigList = f.read().split()
        f.close()
    except:
        f = open(f"config{os.sep}pushdynConfig.conf","w",encoding="UTF-8")
        f.close()
        pushdynConfigList = []
    try:
        f = open(f"config{os.sep}pushliveConfig.conf","r",encoding="UTF-8")
        pushliveConfigList = f.read().split()
        f.close()
    except:
        f = open(f"config{os.sep}pushliveConfig.conf","w",encoding="UTF-8")
        f.close()
        pushliveConfigList = []
    global pushwbConfigDict, pushdynConfigDict, pushliveConfigDict
    pushwbConfigDict = dict()
    pushdynConfigDict = dict()
    pushliveConfigDict = dict()
    
    global wb_uid_set, live_uid_set, dyn_uid_set
    wb_uid_set = set()
    live_uid_set = set()
    dyn_uid_set = set()

    for c in pushwbConfigList:
        push_config = c.split(":")
        push_config[1] = push_config[1].split(",")
        ch_list = []
        for ch in push_config[1]:
            if(len(ch) == 0):
                break
            ch_pair = ch.split(".")
            ch_list.append( (ch_pair[0],ch_pair[1]) )
        pushwbConfigDict[int(push_config[0])] = set(ch_list)
        wb_uid_set.add(int(push_config[0]))

    #print(pushwbConfigDict)
    #print(wb_uid_set)

    for c in pushdynConfigList:
        push_config = c.split(":")
        push_config[1] = push_config[1].split(",")
        ch_list = []
        for ch in push_config[1]:
            if(len(ch) == 0):
                break
            ch_pair = ch.split(".")
            ch_list.append( (ch_pair[0],ch_pair[1]) )
        pushdynConfigDict[push_config[0]] = set(ch_list)
        dyn_uid_set.add(push_config[0])
    
    for c in pushliveConfigList:
        push_config = c.split(":")
        push_config[1] = push_config[1].split(",")
        ch_list = []
        for ch in push_config[1]:
            if(len(ch) == 0):
                break
            ch_pair = ch.split(".")
            ch_list.append( (ch_pair[0],ch_pair[1]) )
        pushliveConfigDict[push_config[0]] = set(ch_list)
        live_uid_set.add(push_config[0])
    
    global last_weibo_time_dict, last_comment_time_dict, last_dynamic_time_dict
    last_weibo_time_dict = dict()
    last_comment_time_dict = dict()
    last_dynamic_time_dict = dict()

    for wbuid in wb_uid_set:
        last_weibo_time_dict[wbuid] = datetime.now()
        last_comment_time_dict[wbuid] = datetime.now()
    for dynuid in dyn_uid_set:
        last_dynamic_time_dict[dynuid] = datetime.now()

async def saveConfig():
    f = open(f"config{os.sep}pushwbConfig.conf","w",encoding="UTF-8")
    for c in pushwbConfigDict.items():
        config_str = f"{c[0]}:"
        for ch in c[1]:
            config_str += f"{ch[0]}.{ch[1]}"
            config_str += ","
        f.write(config_str)
        f.write("\n")
    f.close()
    f = open(f"config{os.sep}pushdynConfig.conf","w",encoding="UTF-8")
    for c in pushdynConfigDict.items():
        config_str = f"{c[0]}:"
        for ch in c[1]:
            config_str += f"{ch[0]}.{ch[1]}"
            config_str += ","
        f.write(config_str)
        f.write("\n")
    f.close()
    f = open(f"config{os.sep}pushliveConfig.conf","w",encoding="UTF-8")
    for c in pushliveConfigDict.items():
        config_str = f"{c[0]}:"
        for ch in c[1]:
            config_str += f"{ch[0]}.{ch[1]}"
            config_str += ","
        f.write(config_str)
        f.write("\n")
    f.close()

def put_guild_channel_msg(guild_id, channel_id, message):
    # print(message)
    data = {
        "guild_id":guild_id,
        "channel_id":channel_id,
        "message":message
    }
    messageQueue.put(data)

# 一个中文字大小为16x16
def doPicTrans(msg, index):
    msg = textwrap.fill(text = msg, width = 20 ,drop_whitespace = False, replace_whitespace = False)
    img = Image.new(mode = 'RGB', size=(330, 10 + (22) * (msg.count('\n') + 1)), color = (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text(xy=(5,5), text=msg, font=font, fill=(0,0,0,255))
    img.save(cur_path + 'TempPic/output'+str(index)+'.png')

def pictureTransform(message):
    toRemove = []
    toPicture = []
    i = 0
    while i < len(message):
        # print(message[i])
        if(message[i].startswith('[CQ')):
            if(len(toPicture) == 0):
                i = i + 1
                continue
            # 把之前toPicture里的转为图片
            # print('toPicture:'+''.join(toPicture))
            doPicTrans(''.join(toPicture), i)
            if(i > 0):
                message.insert(i - 1, '[CQ:image,file=file:///'+cur_path+f'TempPic{os.sep}output'+str(i)+'.png]')
                i = i + 1
            toPicture = []
        else:
            toPicture.append(message[i])
            toRemove.append(message[i])
        i = i + 1
    if(len(toPicture) > 0):
        # print('end toPicture:'+''.join(toPicture))
        doPicTrans(''.join(toPicture), len(message))
        message.append('[CQ:image,file=file:///'+cur_path+f'TempPic{os.sep}output'+str(len(message))+'.png]')
    for content in toRemove:
        message.remove(content)

def messageSender():
    while True:
        message = messageQueue.get(block = True, timeout = None)
        logfile = open('main_log','a', encoding = 'UTF-8')
        logfile.write(time.strftime('%Y-%m-%d %H:%M:%S\n',time.localtime(time.time())))
        try:
            logfile.write('消息内容：' + (''.join(message['message']))+'\n')
            if(sys_str == "Linux"):
                code = os.WEXITSTATUS(os.system("python3 sender.pyw " + str(message['guild_id']) +' '+ str(message['channel_id']) +' "'+ ''.join(message['message'])+'"'+' '+'main_sender_log'))
            else:
                code = os.system("python3 sender.pyw " + str(message['guild_id']) +' '+ str(message['channel_id']) +' "'+ ''.join(message['message'])+'"'+' '+'main_sender_log')
            if code != 0:
                # logfile.write(repr(e) + '\n' + '消息发送失败，尝试加空格')
                # print(repr(e))
                logfile.write('消息发送失败，尝试加空格'+'\n')
                print('消息发送失败，尝试加空格')
                i = len(message['message']) - 1
                while i >= 0:
                    if(message['message'][i].startswith('[') == False):
                        message['message'][i] = message['message'][i] + ' '
                        break
                    i = i - 1
                if(sys_str == "Linux"):
                    code = os.WEXITSTATUS(os.system("python3 sender.pyw " + str(message['guild_id']) +' '+ str(message['channel_id']) +' "'+ ''.join(message['message'])+'"'+' '+'main_sender_log'))
                else:
                    code = os.system("python3 sender.pyw " + str(message['guild_id']) +' '+ str(message['channel_id']) +' "'+ ''.join(message['message'])+'"'+' '+'main_sender_log')
                if code != 0:
                    # logfile.write(repr(e) + '\n' + '消息发送失败，尝试转换为图片')
                    # print(repr(e))
                    logfile.write('消息发送失败，尝试转换为图片'+'\n')
                    print('消息发送失败，尝试转换为图片')
                    originalMessage = ''.join(message['message'])
                    toMessage = message['message']
                    pictureTransform(toMessage)
                    if(sys_str == "Linux"):
                        code = os.WEXITSTATUS(os.system("python3 sender.pyw " + str(message['guild_id']) +' '+ str(message['channel_id']) +' "'+ ''.join(toMessage) +'"'+' '+'main_sender_log'))
                    else:
                        code = os.system("python3 sender.pyw " + str(message['guild_id']) +' '+ str(message['channel_id']) +' "'+ ''.join(toMessage) +'"'+' '+'main_sender_log')
                    if code != 0:
                        # print(repr(e))
                        print('该消息无法发送，已记录'+'\n')
                        f = open('FailedMessage','a', encoding = 'UTF-8')
                        # f.write(repr(e) + '\n')
                        f.write(originalMessage + '\n')
                        f.close()
        except Exception as e:
            logfile.write(repr(e))
        logfile.close()
        sleep(0.1)
        messageQueue.task_done()

def read_config():
    global wb_cookie
    global wb_ua
    try:
        with open('weibo_cookie.txt','r', encoding = 'UTF-8') as f:
            wb_cookie = f.read()
            f.close()
    except Exception as err:
            wb_cookie = ''
            pass
    try:
        with open('weibo_ua.txt','r', encoding = 'UTF-8') as f:
            wb_ua = f.read()
            f.close()
    except Exception as err:
            wb_ua = ''
            pass
    print('wb_cookie:'+wb_cookie)
    print('wb_ua:'+wb_ua)
    loadConfig()

async def main():
    global messageQueue
    messageQueue = queue.Queue(maxsize=-1) # infinity length
    
    senderThread = threading.Thread(target = messageSender)
    senderThread.start()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(ListenLive, 'interval', seconds=71)
    scheduler.add_job(ListenDynamic, 'interval', seconds=91)
    scheduler.start()

    await ListenWeibo()

async def ListenWeibo():
    while True:
        print('查询微博动态...')
        if(len(wb_uid_set) == 0):
            await asyncio.sleep(30)
        for uid in wb_uid_set:
            wb_content = None
            try:
                wb_content = await GetWeibo(uid)
                if(wb_content):
                    for content in wb_content:
                        print('微博内容：' + ''.join(content))
                        for ch in pushwbConfigDict.get(uid, []):
                            put_guild_channel_msg(ch[0], ch[1], content)
            except requests.exceptions.JSONDecodeError as e:
                print("JSON解码错误，可能是502错误，取消该次抓取")
            except Exception as e:
                print(repr(e))
                with open("weibo_error_log", "a", encoding="UTF-8") as f:
                    f.write(time.strftime('%Y-%m-%d %H:%M:%S\n',time.localtime(time.time())))
                    f.write(repr(e) + "\n")
                    f.close()
            await asyncio.sleep(random.random()*37 + 37)

def get_liver_detail(mid):
    res = requests.get('https://api.bilibili.com/x/space/acc/info?mid='+str(mid)+'&jsonp=jsonp', timeout=5)
    res.encoding = 'utf-8'
    res = res.text
    data = json.loads(res)
    data = data['data']
    roomid = 0
    name = ''
    try:
        roomid = data['live_room']['roomid']
        name = data['name']
    except:
        pass
    return {
        "roomid": roomid,
        "name": name
    }

async def ListenLive():
    print('查询直播动态...')
    for uid in live_uid_set:
        await asyncio.sleep(random.random()/5)
        detail = get_liver_detail(uid)
        live_status = await GetLiveStatus(detail['roomid'])
        print(f"id: {uid} status:{live_status[0]} title:{live_status[1]}")
        if(live_status[0] != 0):
            if(live_status[0] == 1):
                content = [detail['name'] + '开播啦！\n直播间标题：' + live_status[1]]
            elif(live_status[0] == -1):
                content = [detail['name'] + '下播了']
            print(''.join(content))
            for ch in pushliveConfigDict.get(uid, []):
                put_guild_channel_msg(ch[0], ch[1], content)

async def GetLiveStatus(uid):
    try:
        res = requests.get('https://api.live.bilibili.com/room/v1/Room/get_info?device=phone&;platform=ios&scale=3&build=10000&room_id=' + str(uid), timeout=2)
    except requests.exceptions.RequestException as e:
        print(repr(e))
        return (0,'')
    res.encoding = 'utf-8'
    res = res.text
    try:
        live_data = json.loads(res)
        live_data = live_data['data']
        now_live_status = str(live_data['live_status'])
        live_title = live_data['title']
    except:
        now_live_status = '0'
        pass
    try:
        with open(cur_path + 'Live/' + str(uid)+'Live','r') as f:
            last_live_str = f.read()
            f.close()
    except Exception as err:
        print(f"UID:{uid} 第一次查询")
        os.makedirs("Live", exist_ok=True)
        f = open(cur_path + 'Live/' + str(uid)+'Live','w')
        f.write(now_live_status)
        f.close()
        return (0,'')
    if(now_live_status != last_live_str):
        f = open(cur_path + 'Live/' + str(uid)+'Live','w')
        f.write(now_live_status)
        f.close()
        if(now_live_status == '1'):
            return (1,live_title)
        else:
            return (-1,'')
    else:
        return (0,'')

async def ListenDynamic():
    print('查询B站动态...')
    for uid in dyn_uid_set:
        dynamic_content = await GetDynamicStatus(uid)
        await asyncio.sleep(1)
        for content in dynamic_content:
            for ch in pushdynConfigDict.get(uid, []):
                put_guild_channel_msg(ch[0], ch[1], content)

async def ModifyPic(pic_path):
    pic = Image.open(pic_path)
    width = pic.size[0]
    height = pic.size[1]
    if((width/height) > 3):
        res = Image.new(mode = 'RGB', size=(width, int(width/3)+1), color = (255, 255, 255))
        res.paste(pic, (0,0,width,height))
        pic_path = pic_path[:-4:] + '_resized.png'
        res.save(pic_path)
    return pic_path

async def GetDynamicContent(dynamic_id):
    async with async_playwright() as p:
        browser = await p.webkit.launch()
        device = p.devices['iPhone 12 Pro']
        context = await browser.new_context(
            **device
            )
        page = await context.new_page()
        await page.set_viewport_size({'width':560, 'height':3500})
        await page.goto('https://m.bilibili.com/dynamic/'+dynamic_id)
        await page.locator('#app > div > div.up-archive').scroll_into_view_if_needed()
        pic_path = cur_path+'TempPic/dynamic_'+dynamic_id+'_screenshot.png'
        await page.locator('#app > div > div.launch-app-btn.card-wrap > div').screenshot(path=pic_path)
        await browser.close()
        return pic_path

async def GetDynamicStatus(uid):
    #print('Debug uid  '+str(uid))
    global last_dynamic_time_dict
    last_dynamic_time = last_dynamic_time_dict[uid]
    print(f'UID:{uid} last_dynamic_time:'+last_dynamic_time.strftime("%Y-%m-%d %H:%M:%S"))
    headers = {
        'Referer': 'https://space.bilibili.com/{user_uid}/'.format(user_uid=uid)
    }
    res = requests.get('https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?host_uid='+str(uid)+'&offset_dynamic_id=0', headers=headers, timeout=5)
    res.encoding='utf-8'
    res = res.text
    #res = res.encode('utf-8')
    cards_data = json.loads(res)
    try:
        cards_data = cards_data['data']['cards']
    except:
        exit()
    # print('Success get')
    index = 0
    content_list=[]
    cards_data[0]['card'] = json.loads(cards_data[0]['card'],encoding='gb2312')

    now_dynamic_time = last_dynamic_time
    # card是字符串，需要重新解析
    while index < len(cards_data):
        #print(cards_data[index]['desc'])
        try:
            dynamic_id = cards_data[index]['desc']['dynamic_id_str']
            # print('nowtime: ' + str(nowtime))
            # print('timestamp: ' + str(cards_data[index]['desc']['timestamp']))
            content = []
            created_time = datetime.fromtimestamp(int(cards_data[index]['desc']['timestamp']))
            if not (last_dynamic_time < created_time): # 不是新动态
                break
            # 以下是处理新动态的内容
            if now_dynamic_time < created_time:
                 now_dynamic_time = created_time
            
            pic_path = await GetDynamicContent(dynamic_id)
            pic_path = await ModifyPic(pic_path)
            content.append('[CQ:image,file=file:///'+pic_path+']')
            content.append('\n')
            """
            if (cards_data[index]['desc']['type'] == 64):
                content.append(bili_name_list[biliindex] +'发了新专栏「'+ cards_data[index]['card']['title'] + '」并说： ' +cards_data[index]['card']['dynamic'])
                content.append('\n')
            else:
                if (cards_data[index]['desc']['type'] == 8):
                    content.append(bili_name_list[biliindex] + '发了新视频「'+ cards_data[index]['card']['title'] + '」并说： ' +cards_data[index]['card']['dynamic'])
                    content.append('\n')
                else:         
                    if ('description' in cards_data[index]['card']['item']):
                        #这个是带图新动态
                        content.append(bili_name_list[biliindex] + '发了新动态： ' +cards_data[index]['card']['item']['description'])
                        content.append('\n')
                        #print('Fuck')
                        #CQ使用参考：[CQ:image,file=http://i1.piimg.com/567571/fdd6e7b6d93f1ef0.jpg]
                        for pic_info in cards_data[index]['card']['item']['pictures']:
                            content.append('[CQ:image,file='+pic_info['img_src']+']')
                            content.append('\n')
                    else:
                        #这个表示转发，原动态的信息在 cards-item-origin里面。里面又是一个超级长的字符串……
                        #origin = json.loads(cards_data[index]['card']['item']['origin'],encoding='gb2312') 我也不知道这能不能解析，没试过
                        #origin_name = 'Fuck'
                        if 'origin_user' in cards_data[index]['card']:
                            origin_name = cards_data[index]['card']['origin_user']['info']['uname']
                            content.append(bili_name_list[biliindex]+ '转发了「'+ origin_name + '」的动态并说： ' +cards_data[index]['card']['item']['content'])
                            content.append('\n')
                        else:
                            #这个是不带图的自己发的动态
                            content_list.append(bili_name_list[biliindex]+ '发了新动态： ' +cards_data[index]['card']['item']['content'])
            """
            content.append('本条动态地址为'+'https://m.bilibili.com/dynamic/'+ cards_data[index]['desc']['dynamic_id_str'])
            content_list.append(content)
        except Exception as err:
                print('PROCESS ERROR')
                print(str(err))
                # traceback.print_exc()
                pass
        index += 1
        if len(cards_data) == index:
            break
        cards_data[index]['card'] = json.loads(cards_data[index]['card']) # 加载下一条动态
    # 更新last_dynamic_time
    print(f'UID:{uid} now_dynamic_time:'+now_dynamic_time.strftime("%Y-%m-%d %H:%M:%S"))
    last_dynamic_time_dict[uid] = now_dynamic_time
    return content_list

def get_long_weibo(weibo_id, headers, is_cut):
    """获取长微博"""
    for i in range(3):
        url = 'https://m.weibo.cn/detail/' + weibo_id
        print('url: '+url)
        html = requests.get(url, headers = headers, timeout=5).text
        html = html[html.find('"status":'):]
        html = html[:html.rfind('"hotScheme"')]
        html = html[:html.rfind(',')]
        html = '{' + html + '}'
        js = json.loads(html, strict=False)
        weibo_info = js.get('status')
        if weibo_info:
            weibo = parse_weibo(weibo_info)
            #截短长微博
            if(is_cut and len(weibo['text']) > 100):
                weibo['text'] = weibo['text'][0:97] + "..."
            print('after cut: ' + weibo['text'])
            return weibo
        time.sleep(random.randint(1, 3))

def parse_weibo(weibo_info):
    weibo = collections.OrderedDict()
    if weibo_info['user']:
        weibo['user_id'] = weibo_info['user']['id']
        weibo['screen_name'] = weibo_info['user']['screen_name']
    else:
        weibo['user_id'] = ''
        weibo['screen_name'] = ''
    #记录用
    weibo['original_text'] = weibo_info['text']

    weibo['text'] = parse_text(weibo_info['text'])[0]

    weibo['pics'] = get_pics(weibo_info)
    #return standardize_info(weibo)
    return weibo

def get_pics(weibo_info):
    """获取微博原始图片url"""
    if weibo_info.get('pics'):
        pic_info = weibo_info['pics']
        pic_list = [pic['large']['url'] for pic in pic_info]
        # pics = ','.join(pic_list)
    else:
        pic_list = []
    return pic_list

def get_created_time(created_at):
    """
    标准化微博发布时间
    if u"刚刚" in created_at:
        created_at = datetime.now()
    elif u"分钟" in created_at:
        minute = created_at[:created_at.find(u"分钟")]
        minute = timedelta(minutes=int(minute))
        created_at = datetime.now() - minute
    elif u"小时" in created_at:
        hour = created_at[:created_at.find(u"小时")]
        hour = timedelta(hours=int(hour))
        created_at = datetime.now() - hour
    elif u"昨天" in created_at:
        day = timedelta(days=1)
        created_at = datetime.now() - day
    elif created_at.count('-') == 1:
        created_at = datetime.now() - timedelta(days=365)
    """
    created_at = datetime.strptime(created_at, '%a %b %d %H:%M:%S %z %Y')
    created_at = created_at.replace(tzinfo=None)
    # print(created_at)
    return created_at

def convert_short_url(url):
    try:
        res = requests.head(url, timeout=5)
        return res.headers.get('location', '')
    except:
        return ''

def parse_text(wb_text):
    wb_soup = BeautifulSoup(wb_text, features="lxml")
    # print(wb_soup)

    all_a = wb_soup.findAll('a')
    pic_list = []
    for a in all_a:
        # print('a:'+str(a))
        pic_link = a.get('href')
        if pic_link == None:
            pic_link = a.getText()
            a.replaceWith(pic_link)
        else:
            # 判断是否为图片
            if pic_link.endswith('.jpg') or pic_link.endswith('.jpeg') or pic_link.endswith('.png') or pic_link.endswith('.gif'):
                # 写入cq码
                # print('[CQ:image,file='+pic_link+']')
                pic_list.append('[CQ:image,file='+pic_link+']')
                a.extract()
            else: # 不是图片
                # 先尝试转一下短链接
                long_url = convert_short_url(pic_link)
                if long_url.endswith('.jpg') or long_url.endswith('.jpeg') or long_url.endswith('.png') or long_url.endswith('.gif'):
                    pic_list.append('[CQ:image,file='+long_url+']')
                    a.extract()
                else:
                    # 是at
                    """
                    if a.getText().startswith('@'):
                        pic_link = a.getText()
                    """
                    # 3.25更改：都提取成文字
                    pic_link = a.getText()
                    a.replaceWith(pic_link)
                

    all_img = wb_soup.findAll('img')
    for img in all_img:
        img_desc = img.get('alt')
        if img_desc == None:
            img_desc = img.getText()
        img.replaceWith(img_desc)

    res = []
    res.append(wb_soup.getText())
    res.append(pic_list)
    
    return res

# 记录下最晚一条被发送的评论的时间
# 爬取按热度排序的第一页评论，如果有符合条件的就发送
# 爬取评论的楼中楼评论，如果有符合条件的就发送
async def GetWeiboComment(weibo_id, mid, headers, uid, content_list, wb_name, weibo_url):
    await asyncio.sleep(random.random() + 7)
    url = 'https://m.weibo.cn/comments/hotflow?'
    params = {
        'id': weibo_id,
        'mid': mid,
        'max_id_type': '0'
    }
    r = requests.get(url, params=params, headers=headers, timeout=5)
    res = r.json()
    global last_comment_time_dict
    now_comment_time = last_comment_time_dict[uid]
    last_comment_time = last_comment_time_dict[uid]
    if res['ok']: # ok为0代表没有评论
        comments = res['data']['data']
        if not comments:
            print(f'UID:{uid} no comment')
            return now_comment_time
        for comment in comments:
            # 符合条件的评论，发送并爬取楼中楼
            # 预先处理，去掉xml
            comment_with_pic = parse_text(comment['text'])

            comment['text'] = comment_with_pic[0]
            comment_pic_list = comment_with_pic[1]
            if comment.get('pic'):
                comment_pic_list.append('[CQ:image,file='+comment['pic']['large']['url']+']')
            
            comment_created_time = get_created_time(comment['created_at'])
            if comment['user']['id'] == uid and last_comment_time < comment_created_time:
                content = []
                # 更新时间记录
                if now_comment_time < comment_created_time:
                    now_comment_time = comment_created_time
                content.append(wb_name + '在' + comment_created_time.strftime("%Y-%m-%d %H:%M:%S") + '发了新评论并说：')
                content.append('\n')
                content.append(comment['text'])
                content.append('\n')
                content.append('原微博地址：'+weibo_url)
                content.append('\n')
                for pic in comment_pic_list:
                    content.append(pic)
                content_list.append(content)
            # 不符合条件的评论，只爬取楼中楼
            # print(type(comment['comments']))
            if not comment['comments']: # 是否存在楼中楼
                continue
            for inner_comment in comment['comments']:
                # print(inner_comment)
                inner_comment_created_time = get_created_time(inner_comment['created_at'])
                if inner_comment['user']['id'] == uid and last_comment_time < inner_comment_created_time:
                    content = []
                    # 更新时间记录
                    if now_comment_time < inner_comment_created_time:
                        now_comment_time = inner_comment_created_time
                    content.append(wb_name + '在' + inner_comment_created_time.strftime("%Y-%m-%d %H:%M:%S") + f"回复了 {comment['user']['screen_name']} 的评论并说：")
                    content.append('\n')

                    # 去除xml
                    inner_comment_with_pic = parse_text(inner_comment['text'])
                    # 记录用
                    inner_comment_original_text = inner_comment['text']

                    inner_comment['text'] = inner_comment_with_pic[0]
                    inner_comment_pic_list = inner_comment_with_pic[1]
                    if inner_comment.get('pic'):
                        inner_comment_pic_list.append('[CQ:image,file='+inner_comment['pic']['large']['url']+']')
                    
                    content.append(inner_comment['text'])
                    content.append('\n')
                    content.append('原评论内容：'+comment['text'])
                    content.append('\n')
                    # 加入回复评论的图片
                    for pic in comment_pic_list:
                        content.append(pic)
                        
                    content.append('\n')
                    content.append('原微博地址：'+weibo_url)
                    content.append('\n')
                    for pic in inner_comment_pic_list:
                        content.append(pic)
                    content_list.append(content)
        # 更新最晚时间
        print(f'UID:{uid} now_comment_time:'+now_comment_time.strftime("%Y-%m-%d %H:%M:%S"))
        # last_comment_time = now_comment_time
    else:
        print("no comment!")
    return now_comment_time

async def GetWeibo(uid):
    global last_weibo_time_dict
    last_weibo_time = last_weibo_time_dict[uid]
    print(f'UID:{uid} last_weibo_time:'+last_weibo_time.strftime("%Y-%m-%d %H:%M:%S"))
    global last_comment_time_dict
    last_comment_time = last_comment_time_dict[uid]
    print(f'UID:{uid} last_comment_time:'+last_comment_time.strftime("%Y-%m-%d %H:%M:%S"))
    content_list=[]
    params = {
        'containerid': '107603' + str(uid)
    }
    url = 'https://m.weibo.cn/api/container/getIndex?'

    headers = {
        'Cookie': wb_cookie,
        'User-Agent': wb_ua
    }
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
    except requests.exceptions.ReadTimeout as e:
        return content_list
    res = r.json()
    if res['ok']:
        weibos = res['data']['cards']
        # 初值
        now_weibo_time = last_weibo_time
        now_comment_time = last_comment_time
        for i in range(min(len(weibos), 1 + 1)):
            w = weibos[i]
            if w['card_type'] == 9:
                retweeted_status = w['mblog'].get('retweeted_status')
                is_long = w['mblog'].get('isLongText')
                weibo_id = w['mblog']['id']
                mid = w['mblog']['mid']
                # 获取用户简介
                user_desc = w['mblog']['user']['description']
                wb_name = w['mblog']['user']['screen_name']
                weibo_url = 'https://m.weibo.cn/detail/' + weibo_id
                weibo_avatar = w['mblog']['user']['avatar_hd']
                content = ['[CQ:image,file='+weibo_avatar+']']
                content.append('\n')
                created_time = get_created_time(w['mblog']['created_at'])
                # 保存要插入在content_list中的位置
                content_index = len(content_list)
                # 查询楼中楼
                comment_created_time = await GetWeiboComment(weibo_id, mid, headers, uid, content_list, wb_name, weibo_url)
                if now_comment_time < comment_created_time:
                    now_comment_time = comment_created_time
                if not (last_weibo_time < created_time): # 不是新微博
                    continue
                # 以下是处理新微博的部分
                # 记录最晚一条微博的时间
                if now_weibo_time < created_time:
                    now_weibo_time = created_time
                if retweeted_status and retweeted_status.get('id'):  # 转发
                    retweet_id = retweeted_status.get('id')
                    is_long_retweet = retweeted_status.get('isLongText')
                    if is_long:
                        weibo = get_long_weibo(weibo_id, headers, False) # 捕捉对象的长微博不截断
                        if not weibo:
                            weibo = parse_weibo(w['mblog'])
                    else:
                        weibo = parse_weibo(w['mblog'])
                    if is_long_retweet:
                        retweet = get_long_weibo(retweet_id, headers, True) # 转发的长微博截断
                        if not retweet:
                            retweet = parse_weibo(retweeted_status)
                    else:
                        retweet = parse_weibo(retweeted_status)
                    weibo['retweet'] = retweet
                    content.append(wb_name + '在' + created_time.strftime("%Y-%m-%d %H:%M:%S") + '转发了微博并说：')
                    content.append('\n')
                    content.append(weibo['text'])
                    content.append('\n')
                    content.append('原微博：'+weibo['retweet']['text'])
                    content.append('\n')
                    # 添加原微博的图片
                    for pic_info in weibo['retweet']['pics']:
                        content.append('[CQ:image,file='+pic_info+']')
                    content.append('\n')
                    content.append('本条微博地址是：' + weibo_url)
                else:  # 原创
                    if is_long:
                        weibo = get_long_weibo(weibo_id, headers, False) # 捕捉对象的长微博不截断
                        if not weibo:
                            weibo = parse_weibo(w['mblog'])
                    else:
                        weibo = parse_weibo(w['mblog'])
                    content.append(wb_name + '在' + created_time.strftime("%Y-%m-%d %H:%M:%S") + '发了新微博并说：')
                    content.append('\n')
                    content.append(weibo['text'])
                    content.append('\n')
                    content.append('本条微博地址是：' + weibo_url)
                    content.append('\n')
                    for pic_info in weibo['pics']:
                        content.append('[CQ:image,file='+pic_info+']')
                content_list.insert(content_index, content)
        print(f'UID:{uid} now_weibo_time:'+now_weibo_time.strftime("%Y-%m-%d %H:%M:%S"))
        # 更新last_weibo_time
        last_weibo_time_dict[uid] = now_weibo_time
        last_comment_time_dict[uid] = now_comment_time
        try:
            UpdateUserDesc(uid, wb_name, user_desc)
        except (NameError, UnboundLocalError):
            pass
    else:
        print(res)
        if(res['errno'] == '100005'):
            print("过于频繁，开始sleep")
            send_mail("微博警告过于频繁", "rt")
            await asyncio.sleep(random.random()*5 + 5)
    return content_list

def send_mail(title, content):
    os.system(f'python3 ../Mail_Sender/mail.py "{title}" "{content}"')

def UpdateUserDesc(uid, wb_name, user_desc):
    try:
        with open(cur_path + 'WeiboDesc/' + str(uid)+'WeiboDesc','r', encoding='UTF-8') as f:
            last_user_desc = f.read()
            f.close()
    except Exception as err:
        os.makedirs("WeiboDesc", exist_ok=True)
        with open(cur_path + 'WeiboDesc/' + str(uid)+'WeiboDesc','w', encoding='UTF-8') as f:
            f.write(user_desc)
            f.close()
        print(f"已创建UID{uid}的微博简介")
        return
    if (user_desc != last_user_desc):
        content = [wb_name + '把简介从\n' + last_user_desc + '\n' + '改成了\n' + user_desc]
        try:
            with open(cur_path + 'WeiboDesc/' + str(uid)+'WeiboDesc','w', encoding='UTF-8') as f:
                f.write(user_desc)
                f.close()
        except Exception as err:
            pass
        for ch in pushwbConfigDict.get(uid, []):
            put_guild_channel_msg(ch[0], ch[1], content)

def cookie_to_dict_list(cookie: str):
    cookie_list = cookie.split(";")
    cookies = []
    for c in cookie_list:
        cookie_pair = c.lstrip().rstrip().split("=")
        cookies.append({
            "name": cookie_pair[0],
            "value": cookie_pair[1],
            "url": "https://weibo.cn"
        })
    return cookies

async def WeiboFollow(uid):
    async with async_playwright() as p:
        browser = await p.webkit.launch()
        device = p.devices['iPhone 12 Pro']
        context = await browser.new_context(
            **device
            )
        await context.add_cookies(cookie_to_dict_list(wb_cookie))
        page = await context.new_page()
        await page.goto("https://weibo.cn/"+str(uid))
        btn_text = await page.text_content("body > div.u > table > tbody > tr > td:nth-child(2) > div > span:nth-child(1) :text('关注')", timeout=5000)
        print(f"UID:{uid} {btn_text}")
        if(btn_text == "加关注"):
            await page.click("body > div.u > table > tbody > tr > td:nth-child(2) > div > span:nth-child(1) :text('关注')", timeout=7000)
            await page.wait_for_timeout(1500)
            print(f"UID:{uid} 已关注")
        await page.wait_for_timeout(3000)
        await browser.close()

async def getAuth(guild_id, user_id):
    message = {
        "guild_id":guild_id,
        "user_id":user_id
    }
    response = requests.post("http://127.0.0.1:5700/get_guild_member_profile", data = message, headers={'Connection':'close'})
    user_data = json.loads(response.text)
    if(user_data['retcode'] == 0):
        roles = user_data['data']['roles']
        for role in roles:
            if(role['role_id'] == '2'):
                return True
    return False

# 以下是命令处理部分
async def dispatcher(websocket, path):
    async for message in websocket:
        msg_data = json.loads(message)
        if(msg_data.get('post_type', "") == 'message' and msg_data.get('message_type', "") == 'guild' and msg_data.get('sub_type', "") == 'channel'):
            # 频道消息
            if(msg_data['guild_id'] in ALLOWED_GUILD):
                content = msg_data['message'].rstrip()
                if(content.startswith(f'[CQ:at,qq={BOT_ID}]')):
                    # 是at bot的消息
                    content = content.replace(f'[CQ:at,qq={BOT_ID}]', '').lstrip()
                    reply = [msg_data['sender']['nickname']+" "]
                    ch = (msg_data['guild_id'], msg_data['channel_id'])
                    print(f"来自频道{ch[0]}的子频道{ch[1]}的{msg_data['sender']['nickname']}的消息：{content}")
                    if(content.startswith("/添加微博推送")):
                        if(await getAuth(msg_data['guild_id'], msg_data['sender']['user_id'])):
                            para_list = content.split()
                            try:
                                int(para_list[1])
                                global pushwbConfigDict
                                if(not (para_list[1] in pushwbConfigDict)):
                                    pushwbConfigDict[para_list[1]] = set()
                                    global wb_uid_set
                                    wb_uid_set.add(para_list[1])
                                    global last_weibo_time_dict, last_comment_time_dict
                                    last_weibo_time_dict[para_list[1]] = datetime.now()
                                    last_comment_time_dict[para_list[1]] = datetime.now()
                                    await WeiboFollow(para_list[1])
                                pushwbConfigDict[para_list[1]].add(ch)
                                reply.append(f"已添加UID为{para_list[1]}的微博推送")
                                await saveConfig()
                            except Exception as e:
                                print(repr(e))
                                reply.append("参数错误！")
                    elif(content.startswith("/添加直播推送")):
                        if(await getAuth(msg_data['guild_id'], msg_data['sender']['user_id'])):
                            para_list = content.split()
                            try:
                                int(para_list[1])
                                global pushliveConfigDict
                                if(not (para_list[1] in pushliveConfigDict)):
                                    pushliveConfigDict[para_list[1]] = set()
                                    global live_uid_set
                                    live_uid_set.add(para_list[1])
                                pushliveConfigDict[para_list[1]].add(ch)
                                reply.append(f"已添加UID为{para_list[1]}的直播推送")
                                await saveConfig()
                            except Exception as e:
                                print(repr(e))
                                reply.append("参数错误！")
                    elif(content.startswith("/添加动态推送")):
                        if(await getAuth(msg_data['guild_id'], msg_data['sender']['user_id'])):
                            para_list = content.split()
                            try:
                                int(para_list[1])
                                global pushdynConfigDict
                                if(not (para_list[1] in pushdynConfigDict)):
                                    pushdynConfigDict[para_list[1]] = set()
                                    global dyn_uid_set
                                    dyn_uid_set.add(para_list[1])
                                    global last_dynamic_time_dict
                                    last_dynamic_time_dict[para_list[1]] = datetime.now()
                                pushdynConfigDict[para_list[1]].add(ch)
                                reply.append(f"已添加UID为{para_list[1]}的动态推送")
                                await saveConfig()
                            except Exception as e:
                                print(repr(e))
                                reply.append("参数错误！")
                    elif(content.startswith("/删除微博推送")):
                        if(await getAuth(msg_data['guild_id'], msg_data['sender']['user_id'])):
                            para_list = content.split()
                            try:
                                int(para_list[1])
                                # global pushwbConfigDict
                                if(para_list[1] in pushwbConfigDict):
                                    try:
                                        pushwbConfigDict[para_list[1]].remove(ch)
                                        if(len(pushwbConfigDict[para_list[1]]) == 0):
                                            # global wb_uid_set
                                            wb_uid_set.remove(para_list[1])
                                            pushwbConfigDict.pop(para_list[1])
                                        reply.append(f"已删除UID为{para_list[1]}的微博推送")
                                        await saveConfig()
                                    except KeyError:
                                        reply.append(f"未添加过UID为{para_list[1]}的微博推送！")
                                else:
                                    reply.append(f"未添加过UID为{para_list[1]}的微博推送！")
                            except Exception as e:
                                print(repr(e))
                                reply.append("参数错误！")
                    elif(content.startswith("/删除直播推送")):
                        if(await getAuth(msg_data['guild_id'], msg_data['sender']['user_id'])):
                            para_list = content.split()
                            try:
                                int(para_list[1])
                                # global pushliveConfigDict
                                if(para_list[1] in pushliveConfigDict):
                                    try:
                                        pushliveConfigDict[para_list[1]].remove(ch)
                                        if(len(pushliveConfigDict[para_list[1]]) == 0):
                                            # global live_uid_set
                                            live_uid_set.remove(para_list[1])
                                            pushliveConfigDict.pop(para_list[1])
                                        reply.append(f"已删除UID为{para_list[1]}的直播推送")
                                        await saveConfig()
                                    except KeyError:
                                        reply.append(f"未添加过UID为{para_list[1]}的直播推送！")
                                else:
                                    reply.append(f"未添加过UID为{para_list[1]}的微博推送！")
                            except Exception as e:
                                print(repr(e))
                                reply.append("参数错误！")
                    elif(content.startswith("/删除动态推送")):
                        if(await getAuth(msg_data['guild_id'], msg_data['sender']['user_id'])):
                            para_list = content.split()
                            try:
                                int(para_list[1])
                                # global pushdynConfigDict
                                if(para_list[1] in pushdynConfigDict):
                                    try:
                                        pushdynConfigDict[para_list[1]].remove(ch)
                                        if(len(pushdynConfigDict[para_list[1]]) == 0):
                                            # global dyn_uid_set
                                            dyn_uid_set.remove(para_list[1])
                                            pushdynConfigDict.pop(para_list[1])
                                        reply.append(f"已删除UID为{para_list[1]}的动态推送")
                                        await saveConfig()
                                    except KeyError:
                                        reply.append(f"未添加过UID为{para_list[1]}的动态推送！")
                                else:
                                    reply.append(f"未添加过UID为{para_list[1]}的微博推送！")
                            except Exception as e:
                                print(repr(e))
                                reply.append("参数错误！")
                    elif(content.startswith("/查询配置")):
                        if(await getAuth(msg_data['guild_id'], msg_data['sender']['user_id'])):
                            reply.append("当前子频道开启的推送如下：\n")
                            reply.append("微博推送：\n")
                            for c in pushwbConfigDict.items():
                                if(ch in c[1]):
                                    reply.append(c[0]+"\n")
                            reply.append("直播推送：\n")
                            for c in pushliveConfigDict.items():
                                if(ch in c[1]):
                                    reply.append(c[0]+"\n")
                            reply.append("动态推送：\n")
                            for c in pushdynConfigDict.items():
                                if(ch in c[1]):
                                    reply.append(c[0]+"\n")
                    elif(content.startswith("/推送帮助")):
                        if(await getAuth(msg_data['guild_id'], msg_data['sender']['user_id'])):
                            reply.append(PUSHHELP)
                    if(len(reply)>1):
                        print(reply)
                        put_guild_channel_msg(ch[0], ch[1], reply)

if __name__ == '__main__':
    read_config()

    asyncio.get_event_loop().create_task(main())
    asyncio.get_event_loop().run_until_complete(websockets.serve(dispatcher, 'localhost', 17235))
    asyncio.get_event_loop().run_forever()
