# -*- coding:utf-8 -*-
"""
    @Time  : 2021/11/10  13:55
    @Author: Feng Lepeng
    @File  : test_get_id_card.py
    @Desc  :
"""

from src.wechat import *
from src.util.mysql_util import MySQLLocal

wx = WeChat()
mysql = MySQLLocal()
start_time = time.time()


def get_id_card():
    # wx.chat_at("test")
    for i in range(8):
        wx.load_more_message(10000)
        print(time.time() - start_time)

    message_list = wx.get_message()
    print(time.time() - start_time)
    get_time = None
    for msg in message_list:
        # print("%s : %s" % (msg[0], msg[1]))
        if msg[0] == "Time":
            get_time = msg[1]
        tmp = re.findall("[\\u4e00-\\u9fa5 ]{0,5}[0-9]{15,18}[\\u4e00-\\u9fa5 ]{0,5}", msg[1])
        if tmp:
            for i in tmp:
                ret = mysql.select("select * from id_card where id_card=%s", (i,))
                if not ret:
                    mysql.insert("insert into id_card(get_time, id_card, message) value(%s, %s, %s)",
                                 (get_time, i, msg[1]))


if __name__ == "__main__":
    get_id_card()
    print(time.time() - start_time)
