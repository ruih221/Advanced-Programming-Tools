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

from models import *
from baseHandler import BaseHandler

from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import mail
from google.appengine.api import images
from google.appengine.ext import blobstore
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
            # logging.info(accessQueue)
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
                sender = 'digest@aptproj.appspotmail.com',
                subject = 'Viewing Digest'
                )
            message.to = mailuser.Id
            message.body = """ 
            Your current mailing frequency is {}
            Top trending sterams are:
            """.format(freqText)
            for trending in trendingStream:
                message.body += trending.name + ' link:' + self.request.host_url + 'view?streamid=' + urllib.quote(trending.name) \
                    + 'views: ' + str(trending.accessFrequency) + '\n'
            message.send()
# [END send_digest]

# [START rebuild_completion_index]
class rebuildCompletionIndex(BaseHandler):
    def get(self):
        allStreams = stream.query(ancestor = streamGroup_key()).fetch()
        meta_data = meta.get_meta()
        completion_index = set()
        for curStream in allStreams:
            completion_index.update(curStream.tags)
            completion_index.add(curStream.name)
        meta_data.completion_index = list(completion_index)
        meta_data.put()


# [END rebuild_completion_index]

class deleteservingurl(BaseHandler):
    def post(self):
        logging.info("deleteservingurl task reached")
        streamkey = ndb.Key(urlsafe=self.request.get("streamkey"))
        cloudImages = Image.query(ancestor = streamkey).fetch()
        for img in cloudImages:
            logging.info("deleteservingurl for loop reached")
            blobkey = img.gcs_key
            images.delete_serving_url(blobkey)
            blobstore.delete(blobkey)
            img.key.delete()