#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# @raidpinbot
#

import telebot, re, os, time
from telebot import types
from logger import get_logger

log = get_logger("bot")

try:
    with open("TOKEN", "r") as tfile: # local run
        TOKEN = tfile.readline().strip('\n')
        print("read token: '%s'" % TOKEN)
        tfile.close()
except FileNotFoundError: # Heroku run
    TOKEN = os.environ['TOKEN']

bot = telebot.TeleBot(TOKEN)

BOT_USERNAME = "raidpinbot"

#
# Bot should pin only raid messages (assume they should have reply_markup keyboard)
#
@bot.message_handler(func=lambda message: 'reply_markup' in message.json)
def check_raidmessage(m):
    log.debug("Delected potential raid message:")
    log.debug(str(m.json))
    is_raid = False
    # series of conditions to detect @RaidBattlesBot inline raid message
    rep_mkup = m.json['reply_markup']
    if 'inline_keyboard' in rep_mkup:
        kb = rep_mkup['inline_keyboard'][0]
        if 'switch_inline_query' in kb[-1]:
            # final check is by 'share' button existence in reply keyboard
            share_button = re.findall(r'^share:.*', kb[-1]['switch_inline_query'])
            if share_button != [] and len(share_button) == 1:
                is_raid = True
    if is_raid:
        log.debug("Raid message confirmed, pinning")
        time.sleep(1)
        bot.pin_chat_message(m.chat.id, m.message_id)
        log.debug("Message pinned: %s" % m.text)
    else:
        log.error("Not a raid message, skipping")

bot.polling(none_stop=True, interval=0, timeout=20)
