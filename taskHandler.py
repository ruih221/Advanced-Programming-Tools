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

from models import stream, userSub, mailingListUser
from baseHandler import BaseHandler

from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import mail
# [END imports]

DEFAULT_TIME_INTERVAL = 5

def updateLeaderboard(BaseHandler):
    def get(self):
        allStreams = stream.query()
        # all date time older than this will be dropped
        cutoffDT = datetime.datetime.now() - datetime.timedelta(seconds=10)
        for curStream in allStreams:
            accessQueue = curStream.accessQueue
            while (len(accessQueue) != 0 and accessQueue[0] < cutoffDT):
                accessQueue.pop(0)
                curStream.accessFrequency -= 1

def senddigest(BaseHandler):
    def get(self):
        path = self.request.path
        frequency = re.seasrch(r'.*(\d+)', path)
        frequency = frequency.group(0)
        mailUsers = mailingListUser.query(mailingListUser.frequency == frequency)
        trendingStream = stream.query().order(-steam.accessFrequency).fetch(3)
        for mailuser in mailUsers:
            message = mail.EmailMessage(
                sender = 'digest@aptproj.appspotmail.com',
                subject = 'Viewing Digest'
                )
            message.to = mailuser.Id
            message.body = """ 
                Your current mailing frequency is {}
                Top trending sterams are:
            """.format(frequency)
            for trending in treandingStream:
                message.body += trending.name + ' link:' + sef.request.host_url + 'view?streamid=' + urllib.quote(trending.name) \
                    + 'views: ' + trending.accessFrequency
            message.send()
                


        

