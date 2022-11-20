#!/usr/bin/python

import json
# 轮询推送服务
import queue
import time

from commons.dispatcher import dispatcher
from configs import language_config
from configs import discord_config
from defines import event_type
from defines import message_type
from servers import service
from utils.logger import logger
from discordwebhook import Discord


class DingdingPushService(service.Service):
    __message_queue = queue.Queue()  # 推送队列
    __webhook = Discord(url=discord_config.WEBHOOK_URL)

    def __init__(self):
        super().__init__()

    def _onUpdate(self):
        while (not self.__message_queue.empty()):
            msg = self.__message_queue.get()
            msg_type = msg['type']
            msg_title = msg['title']
            msg_text = msg['text']
            logger.info('【推送服务机{type}】准备推送:【{title}】'.format(type=msg_type, title=msg_title))
            self.__webhook.post(content=msg_text)

    def __push_message(self, msg):
        msg_type = msg['type']
        msg_item = msg['item']

        title, text = None, None
        if msg_type == message_type.MessageType.Dynamic:
            title, text = self.__convert_dynamic_content_to_message(msg_item)
        elif msg_type == message_type.MessageType.Live:
            title, text = self.__convert_live_status_content_to_message(msg_item)
        elif msg_type == message_type.MessageType.Notice:
            title, text = self.__convert_dynamic_content_to_message(msg_item)

        if title and text:
            self.__message_queue.put({
                'type': msg_type,
                'title': title,
                'text': text
            })

    # 将内容转换成消息推送
    def __convert_dynamic_content_to_message(self, item):
        uid = item['desc']['uid']
        uname = item['desc']['user_profile']['info']['uname']
        dynamic_type = item['desc']['type']
        dynamic_id = item['desc']['dynamic_id']
        timestamp = item['desc']['timestamp']
        dynamic_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        card_str = item['card']
        card = json.loads(card_str)

        content = ''
        pic_tags = ''
        if dynamic_type == 1:
            # 转发动态
            content = card['item']['content']
        elif dynamic_type == 2:
            # 图文动态
            content = card['item']['description']
            pic_url = card['item']['pictures'][0]['img_src']
            pic_tags = "![pic]({pic_url})".format(pic_url=pic_url)
        elif dynamic_type == 4:
            # 文字动态
            content = card['item']['content']
        elif dynamic_type == 8:
            # 投稿动态
            content = card['title']
            pic_url = card['pic']
            pic_tags = "![pic]({pic_url})".format(pic_url=pic_url)
        elif dynamic_type == 64:
            # 专栏动态
            content = card['title']
            pic_url = card['image_urls'][0]
            pic_tags = "![pic]({pic_url})".format(pic_url=pic_url)

        return language_config.get_string(1000001, name=uname), language_config.get_string(1000002, name=uname,
                                                                                           content=content,
                                                                                           pic_tags=pic_tags,
                                                                                           dynamic_id=dynamic_id)

    def __convert_live_status_content_to_message(self, content):
        name = content['data']['name']
        room_id = content['data']['live_room']['roomid']
        room_title = content['data']['live_room']['title']
        room_cover_url = content['data']['live_room']['cover']
        pic_tags = "![pic]({pic_url})".format(pic_url=room_cover_url)

        return language_config.get_string(1000003, name=name), language_config.get_string(1000004, name=name,
                                                                                          content=room_title,
                                                                                          pic_tags=pic_tags,
                                                                                          room_id=room_id)

    def _onStart(self):
        dispatcher.add_event_listener(event_type.MESSAGE_PUSH, self.__push_message)

    def _onExit(self):
        dispatcher.remove_event_listener(event_type.MESSAGE_PUSH, self.__push_message)
