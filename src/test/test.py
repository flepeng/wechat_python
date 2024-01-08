# -*- coding:utf-8 -*-
"""
    @Time  : 2021/11/10  13:55
    @Author: Feng Lepeng
    @File  : test.py
    @Desc  :
"""
from src.wechat import *

wx = WeChat()


def test_get_seeion_list():
    ret = wx.get_session_list()  # 获取会话列表
    print("当前的会话列表：{}".format(ret))


def test_get_message():
    # 输出当前聊天窗口聊天消息,倒叙输出
    message_list = wx.get_message()
    for msg in message_list:
        print("%s : %s" % (msg[0], msg[1]))

    # 获取更多聊天记录
    wx.load_more_message(10)
    message_list = wx.get_message()
    for msg in message_list:
        print("%s : %s" % (msg[0], msg[1]))


def test_send_message():
    # 向某人发送消息，这个人必须是全部名称，否则发送失败
    message = "工作你好，这是一个测试"
    who = "文件传输"
    wx.send_message(who, message)


def test_send_multiple_message():
    # 发送换行消息，有两种方式
    message1 = """你好{ctrl}{enter}
这是第二行{ctrl}{enter}"""
    message2 = """你好
这是第二行
    """
    who = "文件传输"

    # 第一种
    wx.send_message(who, message1)

    # 第二种：将内容复制到剪贴板，类似于Ctrl+C，然后Ctrl+V
    WeChatUtil.copy_to_clipboard(message2)
    wx.send_message(who, "{Ctrl}v")


def test_send_picture():
    # 向某人发送程序截图
    who = "文件传输"
    name = "微信"
    classname = "WeChatMainWndForPC"
    wx.screenshot_and_copy_to_clipboard(classname=classname)  # 发送微信窗口的截图给文件传输助手
    wx.send_message(who, "{Ctrl}v")


if __name__ == "__main__":
    test_get_message()
    # test_send_message()
    # test_send_multiple_message()
    # test_get_history_message()
