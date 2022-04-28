# Dynamic_Monitor
如果有时间会更新功能的，Bug尽量及时修复。
## 感谢
- QQBot_bilibili https://github.com/wxz97121/QQBot_bilibili
- blivedm https://github.com/xfgryujk/blivedm
- go-cqhttp https://github.com/Mrs4s/go-cqhttp
## 使用
运行main.py即可
## 配置
- 需要在main.py中配置Bot在QQ频道的id和需要开启推送功能的频道id
- B站抓取延迟在main()中可以修改，微博抓取延迟在GetWeibo()中可以修改
- 注意：尽量不要修改太低以免触发反爬措施！
## 需求
- Python 3.8 和所需要的包
- go-cqhttp
## 注意
- 请根据自己的系统环境更改字体文件路径！
- 若要捕获粉丝可见微博，需要在根目录配置Cookie：weibo_cookie.txt Cookie获取方式：https://github.com/dataabc/weiboSpider/blob/master/docs/cookie.md
- 建议同时配置抓取时使用的UA（User-Agent）：weibo_ua.txt
