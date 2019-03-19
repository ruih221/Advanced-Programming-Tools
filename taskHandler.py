# [START imports]
import cgi
import webapp2
import cloudstorage as gcs

import os
import logging
import json
import datetime
import urllib
import re

from models import stream, userSub, mailingListUser, streamGroup_key, mailingUser_group
from baseHandler import BaseHandler

from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import mail
# [END imports]

DEFAULT_TIME_INTERVAL = 5

# [START update_leader_board]
class updateLeaderboard(BaseHandler):
    def get(self):
        allStreams = stream.query(ancestor = streamGroup_key()).fetch()
        # all date time older than this will be dropped
        cutoffDT = datetime.datetime.now() - datetime.timedelta(hours=1)
        for curStream in allStreams:
            accessQueue = curStream.accessQueue
            logging.info(accessQueue)
            while (len(accessQueue) != 0 and accessQueue[0] < cutoffDT):
                accessQueue.pop(0)
            curStream.accessFrequency = len(accessQueue)
            curStream.put()
# [END update_leader_board]

# [START send_digest]
class senddigest(BaseHandler):
    def get(self):
        path = self.request.path
        frequency = re.search(r'.*senddigest(\d+)', path)
        frequency = int(frequency.group(1))
        if frequency == 5:
            freqText = '5 minutes'
        if frequency == 60:
            freqText = '60 minutes'
        if frequency == 24:
            freqText = '1 day'
        mailUsers = mailingListUser.query(ancestor = mailingUser_group(frequency)).fetch()
        trendingStream = stream.query(ancestor = streamGroup_key()).order(-stream.accessFrequency).fetch(3)
        for mailuser in mailUsers:
            message = mail.EmailMessage(
                sender = 'digest@streamshare.appspotmail.com',
                subject = 'Viewing Digest'
                )
            message.to = mailuser.Id
            message.body = """ 
            Your current mailing frequency is {}
            Top trending sterams are:
            """.format(freqText)
            for trending in trendingStream:
                message.body += trending.name + ' link:' + self.request.host_url + 'view?streamid=' + urllib.quote(trending.name) \
                    + 'views: ' + str(trending.accessFrequency)
            message.send()
# [END send_digest]


        

