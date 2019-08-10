#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# @raidpinbot
#

import telebot, re, os, time
import cherrypy
from telebot import types
from logger import get_logger

BOT_USERNAME = 'raidpinbot'
WEBHOOK_HOST = BOT_USERNAME + '.herokuapp.com'
WEBHOOK_PORT = 8443  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = '0.0.0.0'  # In some VPS you may need to put here the IP addr

WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Path to the ssl private key

log = get_logger("bot")

try:
    with open("TOKEN", "r") as tfile: # local run
        TOKEN = tfile.readline().strip('\n')
        print("read token: '%s'" % TOKEN)
        tfile.close()
except FileNotFoundError: # Heroku run
    TOKEN = os.environ['TOKEN']

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % TOKEN

bot = telebot.TeleBot(TOKEN)

# WebhookServer, process webhook calls
class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
           'content-type' in cherrypy.request.headers and \
           cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)

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


# Remove webhook, it fails sometimes the set if there is a previous webhook
bot.remove_webhook()

# Set webhook
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))

# Disable CherryPy requests log
access_log = cherrypy.log.access_log
for handler in tuple(access_log.handlers):
    access_log.removeHandler(handler)

# Start cherrypy server
cherrypy.config.update({
    'server.socket_host'    : WEBHOOK_LISTEN,
    'server.socket_port'    : WEBHOOK_PORT,
    'server.ssl_module'     : 'builtin',
    'server.ssl_certificate': WEBHOOK_SSL_CERT,
    'server.ssl_private_key': WEBHOOK_SSL_PRIV
})

cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})
# bot.polling(none_stop=True, interval=0, timeout=20)
