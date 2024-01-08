# -*- coding:utf-8 -*-
"""
    @Time  : 2021/11/10  13:55
    @Author: Feng Lepeng
    @File  : wechat.py
    @Desc  :
"""
import os
import time
import win32gui
import win32con
import re

from io import BytesIO
import pyscreenshot as shot
import uiautomation as uia
import win32clipboard as wc
from PIL import ImageGrab


class WeChatParam:
    SYS_TEXT_HEIGHT = 33
    TIME_TEXT_HEIGHT = 34
    RECALL_TEXT_HEIGHT = 45


class WeChatUtil:

    @staticmethod
    def copy_to_clipboard(data, dtype='text'):
        """
        复制文本信息或图片到剪贴板
        :param data: 要复制的内容，str 或 Image 图像
        """
        if dtype.upper() == 'TEXT':
            type_data = win32con.CF_UNICODETEXT
        elif dtype.upper() == 'IMAGE':
            type_data = win32con.CF_DIB
            output = BytesIO()
            data.save(output, 'BMP')
            data = output.getvalue()[14:]
        else:
            raise ValueError('param (dtype) only "text" or "image" supported')
        wc.OpenClipboard()
        wc.EmptyClipboard()
        wc.SetClipboardData(type_data, data)
        wc.CloseClipboard()

    @staticmethod
    def screenshot(handle):
        """
        为句柄 handle 的程序截图
        :param handle: 句柄
        """
        bbox = win32gui.GetWindowRect(handle)
        print(bbox)
        win32gui.SetWindowPos(handle, win32con.HWND_TOPMOST, 0, 0, 0, 0, \
                              win32con.SWP_SHOWWINDOW | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        win32gui.SetWindowPos(handle, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, \
                              win32con.SWP_SHOWWINDOW | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        win32gui.BringWindowToTop(handle)
        im = shot.grab(bbox)
        # im = ImageGrab.grab(bbox)
        print(im)
        return im

    @staticmethod
    def format_message(message_item):
        """
        格式化消息
        :param message_item:
        :return:
        """

        def judge_type(message):
            if '撤回' in message:
                ret = ('Recall', message)
            elif re.findall("[0-9]{1,2}:[0-9]{1,2}", message):
                ret = ('Time', message)
            else:
                ret = ('SYS11', message)
            return ret

        uia.SetGlobalSearchTimeout(0)
        message_item_name = message_item.Name
        if message_item.BoundingRectangle.height() == WeChatParam.SYS_TEXT_HEIGHT:
            ret = judge_type(message_item_name)
        elif message_item.BoundingRectangle.height() == WeChatParam.TIME_TEXT_HEIGHT:
            ret = ('Time', message_item_name)
        elif message_item.BoundingRectangle.height() == WeChatParam.RECALL_TEXT_HEIGHT:
            ret = judge_type(message_item_name)
        else:
            index = 1
            tmp = message_item.ButtonControl(foundIndex=index)
            try:
                while True:
                    if tmp.Name == '':
                        index += 1
                        tmp = message_item.ButtonControl(foundIndex=index)
                    else:
                        break
                ret = (tmp.Name, message_item_name)
            except:
                ret = judge_type(message_item_name)
        uia.SetGlobalSearchTimeout(10.0)
        return ret


class WeChat:
    def __init__(self):
        self.window = uia.WindowControl(ClassName='WeChatMainWndForPC')
        self.histroy_window = uia.WindowControl(ClassName='FileManagerWnd')
        self.session_control = self.window.ListControl(Name='会话')
        self.search_control = self.window.EditControl(Name='搜索')
        self.MsgList = self.window.ListControl(Name='消息')
        self.SessionItemList = []

    def get_session_list(self, reset=False):
        """
        获取当前会话列表，更新会话列表
        """
        self.SessionItem = self.session_control.ListItemControl()
        if reset:
            self.SessionItemList = []
        for i in range(100):
            try:
                name = self.SessionItem.Name
            except:
                break
            if name not in self.SessionItemList:
                self.SessionItemList.append(name)
            self.SessionItem = self.SessionItem.GetNextSiblingControl()
        return self.SessionItemList

    def get_last_message(self):
        """
        获取当前窗口中最后一条聊天记录
        """
        uia.SetGlobalSearchTimeout(1.0)
        message_item = self.MsgList.GetChildren()[-1]
        Msg = WeChatUtil.format_message(message_item)
        uia.SetGlobalSearchTimeout(10.0)
        return Msg

    def load_more_message(self, wheel_times):
        """
        定位到当前聊天页面，并往上滚动鼠标滚轮，加载更多聊天记录到内存
        """
        n = 1 if wheel_times < 0.1 else wheel_times
        self.MsgList.WheelUp(wheelTimes=int(wheel_times), waitTime=0.01)

    def get_history_message(self):
        item_list = self.histroy_window.ListControl(Name="全部")
        print(item_list.Name)
        item = item_list.ListItemControl()
        print(item.Name)
        for i in range(100):
            print(item.TextControl().Name)
            item = item.GetNextSiblingControl()

    def get_message(self):
        """
        获取当前窗口中加载的所有聊天记录
        """
        message_list = []
        for message in self.MsgList.GetChildren():
            message_list.append(WeChatUtil.format_message(message))
        return message_list

    def search(self, keyword):
        """
        查找微信好友或关键词
        :param keywords: 要查找的关键词，必须是完整匹配
        """
        self.window.SetFocus()
        time.sleep(0.2)
        self.window.SendKeys('{Ctrl}f', waitTime=1)
        self.search_control.SendKeys(keyword, waitTime=1.5)
        self.search_control.SendKeys('{Enter}')

    def session_wheel_done(self, who, wheel_times):
        """
        会话列表下滑查找对应的联系人，找到之后点击该联系人
        """
        for i in range(wheel_times):
            if who not in self.get_session_list():
                self.session_control.WheelDown(wheelTimes=3, waitTime=0.1 * i)
            else:
                time.sleep(0.5)
                self.session_control.ListItemControl(SubName=who).Click(simulateMove=False)
                return True

    def chat_at(self, who, wheel_times=None):
        """
        打开某个聊天框
        :param who: 消息的接受人，最好是全匹配，模糊匹配只匹配搜索到的第一个
        :param wheel_times: 向下滚动多少次
        """
        self.window.SwitchToThisWindow()
        wheel_times = 10 if not wheel_times else wheel_times
        ret = self.session_wheel_done(who, wheel_times)
        if ret:
            return True
        else:
            self.search(who)
            return self.session_wheel_done(who, 1)

    def send_message(self, who, message, clear=True):
        """
        向 who 发送消息
        :param who: 消息的接受人，最好是全匹配，模糊匹配只匹配搜索到的第一个
        :param msg: 要发送的消息
        :param clear: 是否清除当前已编辑内容
        """
        self.chat_at(who)

        input_control = self.window.EditControl(SubName=who)
        if clear:
            input_control.SendKeys('{Ctrl}a', waitTime=0)
        input_control.SendKeys(message, waitTime=0)
        input_control.SendKeys('{Enter}', waitTime=0)

    def send_files(self, who, file, not_exists='ignore'):
        """
        向当前聊天窗口发送文件
        not_exists: 如果未找到指定文件，继续或终止程序
        filepath (list): 要复制文件的绝对路径
        """
        file = os.path.realpath(file)
        if not os.path.exists(file):
            if not_exists.upper() == 'IGNORE':
                print('File not exists:', file)
            elif not_exists.upper() == 'RAISE':
                raise FileExistsError('File Not Exists: %s' % file)
            else:
                raise ValueError('param not_exists only "ignore" or "raise" supported')
        key = '<EditElement type="3" filepath="%s" shortcut="" />' % file

        input_control = self.window.EditControl(SubName=who)
        input_control.SendKeys(' ', waitTime=0)
        input_control.SendKeys('{Ctrl}a', waitTime=0)
        input_control.SendKeys('{Ctrl}c', waitTime=0)
        input_control.SendKeys('{Delete}', waitTime=0)

        while True:
            try:
                data = WeChatUtil.CopyDict()
                break
            except:
                pass

        for i in data:
            data[i] = data[i].replace(b'<EditElement type="0"><![CDATA[ ]]></EditElement>', key.encode())

        data1 = {
            '13': '',
            '16': b'\x04\x08\x00\x00',
            '1': b'',
            '7': b''
        }
        data.update(data1)

        wc.OpenClipboard()
        wc.EmptyClipboard()
        for k, v in data.items():
            wc.SetClipboardData(int(k), v)
        wc.CloseClipboard()
        self.send_clipboard()
        return 1

    def send_clipboard(self):
        """向当前聊天页面发送剪贴板复制的内容"""
        self.send_message('{Ctrl}v')

    def screenshot_and_copy_to_clipboard(self, name=None, classname=None):
        """
        发送某个桌面程序的截图(如微信)到剪贴板，不支持扩展屏的截图。
        :param name: 要发送的桌面程序名字，如：微信
        :param classname: 要发送的桌面程序类别名，一般配合 spy 小工具使用，以获取类名，如：微信的类名为 WeChatMainWndForPC
        """
        if not name and not classname:
            return False

        handle = win32gui.FindWindow(classname, name)
        if not handle:
            return False

        ret_image = WeChatUtil.screenshot(handle)
        WeChatUtil.copy_to_clipboard(ret_image, 'image')
        return True


if __name__ == '__main__':
    wx = WeChat()
    ret = wx.get_session_list()  # 获取会话列表
    print("当前的会话列表：{}".format(ret))
