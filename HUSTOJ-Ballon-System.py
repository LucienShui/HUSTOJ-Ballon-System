# @author EndangeredFish    LucienShui    hamburger
# -*- coding:utf-8 -*-
import requests
import re
import queue
import threading
import time
from pprint import pprint as pp

# 以下可修改

## HUSTOJ地址
web = "http://acm.upc.edu.cn/oj/"

## 比赛ID
contestid = ""

## 账号
uid = ""

## 密码
upswd = ""

# 需要筛选的ID前缀
preid = ""

## 正则表达式模式串
# pattern = "<tr class='(even|odd)row'><td>([0-9]+)</td><td><a href='userinfo\.php\?user=([a-zA-Z0-9_]+)'>([a-zA-Z0-9_]+)</a></td><td><div class=center><a href='problem\.php\?id=(\d+)'>(\d+)</a></div></td><td><span class='btn btn-success'>(\*?)正确</span>"
userpattern = "(" + preid + "[a-zA-Z0-9_]+)"
pattern = "<tr class='(evenrow|oddrow)'><td>(\d+)</td><td><a href='contestrank\.php\?cid=1001&user_id=" + userpattern + "#" + userpattern+ "'>" + userpattern + "</a></td><td><div class=center><a href='problem\.php\?cid=1001&pid=(\d)'>([A-Za-z])</div></a></td><td><span class='hidden' style='display:none' result='4' ></span><span class='btn btn-success'  title='答案正确，请再接再厉。'>(\*?)正确"

urllogin = web + "login.php"  # 登陆地址
urlstatus = web + "status.php?problem_id=&user_id=&cid=" + contestid + "&language=-1&jresult=4"  # 榜单地址
data = {"user_id": uid, "password": upswd}  # 登录信息

headers = {"Accept": "text/html,application/xhtml+xml,application/xml;",
           "Accept-Encoding": "gzip",
           "Accept-Language": "zh-CN,zh;q=0.8",
           "Referer": web,
           "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36"
           }


def producer(out_q, data):
    while True:
        out_q.put(data)


def login():
    reslogin = requests.post(urllogin, data=data, headers=headers)
    return reslogin.cookies


def getstatus(cookies_):
    responstatus = requests.get(urlstatus, cookies=cookies_, headers=headers)
    return responstatus.content.decode('utf-8')


def appear(tmp, list):
    for each in list:
        if each['user'] == tmp['user'] and each['problem'] == tmp['problem']: return True
    return False


def showList(Ballon_list, vis):
    cnt = 0
    outstr = ""
    for tmp in Ballon_list:
        flag = True
        for each in vis:
            if tmp['ballon_id'] == each:
                flag = False
        if flag:
            outstr = outstr + ("%3d" % (tmp['ballon_id'])) + ' ' + ' ' + str(tmp['problem']) + ' ' + str(
                tmp['user']) + '\n'
            cnt = cnt + 1
        if cnt == 10: break
    print(outstr)


class mainThread(threading.Thread):
    def __init__(self, work_queue):
        super().__init__()  # 必须调用
        self.work_queue = work_queue
        threading.Thread.__init__(self)

    def run(self):
        # 最新runID
        currentRunID = 0
        cookies = login()
        Ballon_number = 1
        rawlist = []
        while True:
            # 未处理用户列表
            html = getstatus(cookies)
            rawresult = re.findall(pattern, html, re.S)  # list
            addNew = False
            for each in reversed(rawresult):
                tmp = {'ballon_id': Ballon_number, 'user': each[2], 'problem': each[6]}
                if eval(each[1]) > currentRunID:
                    if not appear(tmp, rawlist):
                        addNew = True
                        rawlist.append(tmp)
                        Ballon_number = Ballon_number + 1
            if addNew:
                print("New status!!!")
            while not self.work_queue.empty():
                self.work_queue.get()
            self.work_queue.put(rawlist)  # 多线程通信
            time.sleep(1)


class watchdogThread(threading.Thread):
    def __init__(self, work_queue):
        super().__init__()
        self.work_queue = work_queue

    def run(self):
        Ballon_list = self.work_queue.get()
        alreadySend = []
        vis = []
        showList(Ballon_list, vis)
        while True:
            try:
                index = eval(input())
                if index > 0:
                    cnt = 0
                    for tmp in Ballon_list:
                        if index == tmp['ballon_id']:
                            vis.append(index)
                            alreadySend.append(Ballon_list[cnt])
                            break
                        cnt = cnt + 1
                    Ballon_list = self.work_queue.get()
                    showList(Ballon_list, vis)
                elif index == 0:
                    Ballon_list = self.work_queue.get()
                    showList(Ballon_list, vis)
                else:
                    for tmp in reversed(alreadySend): print(tmp)
            except:
                Ballon_list = self.work_queue.get()
                showList(Ballon_list, vis)
                print("No!")


def main():
    work_queue = queue.Queue()
    thread1 = mainThread(work_queue=work_queue)
    thread1.daemon = True
    thread1.start()
    time.sleep(3)
    watchdog = watchdogThread(work_queue=work_queue)
    watchdog.daemon = True
    watchdog.start()
    work_queue.join()


if __name__ == '__main__':
    main()
