# [START imports]
import cgi
import webapp2
import cloudstorage as gcs

import os
import logging
import urllib
from urlparse import urlparse
import json

from models import stream, userSub
from baseHandler import BaseHandler

from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import app_identity
from google.appengine.api import search
# [END imports]

DEFAULT_STREAM_NAME = 'public stream'
DEFAULT_PAGE_RANGE = 4
DEFAULT_KITTEN = 'https://storage.googleapis.com/aptproj.appspot.com/defaultkitten.jpg'

def get_stream_key(stream_name=DEFAULT_STREAM_NAME):
  return ndb.Key('stream', stream_name)

#[START management_page]
class Management(BaseHandler):
  @BaseHandler.check_log_in
  def get(self):
    user = users.get_current_user()
    subscribedStream = userSub.query(userSub.Id == user.email()).get().subscribedStream
    ownedStream = stream.query(stream.owner == user.email())
    # code needed after front end is finished
    self.render_template('management.html', {})
#[END management_page]

#[START create_new_stream]
class CreateNewStream(BaseHandler):
  def post(self):
    user = users.get_current_user()
    NewStreamName = self.request.get('name')
    if stream.query(stream.name == NewStreamName).get() != None:
      # need to modify later to redirect to error page
      self.response.write("already exist")
    
    tag = self.request.get('tags')
    # remove white space and # sign
    tag = [x.strip()[1:] for x in tag.split(',')]
    owner = user.email()
    cover = self.request.get('cover', default_value = DEFAULT_KITTEN)
    newStream = stream(name = NewStreamName, tags = tag, owner = owner, cover = cover)
    newStream.put()
    # handle subscription later here
    self.redirect('/manage')
#[END create_new_stream]

#[START new_stream]
class newStream(BaseHandler):
  @BaseHandler.check_log_in
  def get(self):
    self.render_template('newstream.html', {})
#[END new_stream]

#[START searchStream]
class searchStream(webapp2.RequestHandler):
  def get(self):
    pass


#[END searchStream]

#[START upload_image]
class UploadImage(BaseHandler):
  def post(self):
    images = self.request.POST.getall('file')
    streamId = self.request.get('streamid')
    bucket_name = os.environ.get('BUCKET_NAME',
                               app_identity.get_default_gcs_bucket_name())
    write_retry_params = gcs.RetryParams(backoff_factor=1.1)
    #TODO: add duplicate detection
    for img in images:
      fileName = '/' + bucket_name + '/' + streamId + '/' + img.filename
      gcs_file = gcs.open(fileName, 
                          'w',
                          content_type = img.type,
                          retry_params = write_retry_params)
      gcs_file.write(img.file.read())
      gcs_file.close()
#[END upload_image]

#[START get_more_images]
def getMoreImages(streamId, pageRange = DEFAULT_PAGE_RANGE, markers=''):
  bucket_name = os.environ.get('BUCKET_NAME',
                               app_identity.get_default_gcs_bucket_name())
  streamPath = '/' +bucket_name + '/' + streamId
  imageUrls = []
  publicAccesAPI = 'https://storage.googleapis.com'
  try:
    images = gcs.listbucket(streamPath, max_keys = pageRange, marker = markers)
  except:
    return None
  
  for img in images:
    imageUrls.append(publicAccesAPI + urllib.quote(img.filename))
  
  return imageUrls
#[END get_more_images]

#[START load_more]
class loadMore(BaseHandler):
  def get(self):
    streamId = self.request.get('streamid')
    marker = self.request.get('marker')
    marker = urlparse(marker).path
    marker = urllib.unquote(marker)
    imgList = getMoreImages(streamId = streamId, markers = marker)
    # send response back as json 
    self.response.write(json.dumps({'images' : imgList}))

#[END load_more]

#[START View]
class View(BaseHandler):
  @BaseHandler.check_log_in
  def get(self):
    streamId = self.request.get("streamid")
    pageRange = self.request.get("pagerange", default_value = DEFAULT_PAGE_RANGE)
    imgUrls = []
    if streamId:
      imgUrls = getMoreImages(streamId, pageRange)
    template_values = {
      'streamId' : streamId,
      'imageUrls' : imgUrls
    }
    self.render_template('view.html', template_values)
#[END View]


#[START main_page]
class MainPage(BaseHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      self.redirect('manage')
      subscribedStream = userSub.query(userSub.Id == user.email()).get()

      # create user subscription if not already created 
      if subscribedStream == None:
        sub = userSub(Id = user.email(), subscribedStream = [])
        sub.put()
      return
    else:
      url = users.create_login_url(self.request.uri)
      url_linktext = 'Login with Google'
      
    self.render_template('index.html', {})
# [END main_page]