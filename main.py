# [START imports]
import cgi
import jinja2
import webapp2
import cloudstorage as gcs

import os
import logging
import urllib
from urlparse import urlparse
import json

from models import stream, userSub

from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import app_identity

JINJA_ENVIRONMENT = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
  extensions=['jinja2.ext.autoescape'],
  autoescape=True
)

# [END imports]


DEFAULT_STREAM_NAME = 'public stream'
DEFAULT_PAGE_RANGE = 4
def get_stream_key(stream_name=DEFAULT_STREAM_NAME):
  return ndb.Key('stream', stream_name)

#[START management_page]
class Management(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      userId = user.email()
      url = users.create_logout_url('/')
      url_linktext = 'Logout'
      subscribedStream = userSub.query(userSub.Id == user.email()).get()

      # create user subscription if not already created 
      if subscribedStream == None:
        sub = userSub(Id = user.email(), subscribedStream = [])
        sub.put()
    else:
      self.redirect('/')
      return

    subscribedStream = userSub.query(userSub.Id == user.email()).get().subscribedStream
    ownedStream = stream.query(stream.owner == user.email())
    # code needed after front end is finished
    
    template_values = {
      'url' : url,
      'url_linktext' : url_linktext
    }
    template = JINJA_ENVIRONMENT.get_template('management.html')
    self.response.write(template.render(template_values))
#[END management_page]

#[START create_new_stream]
class CreateNewStream(webapp2.RequestHandler):
  def post(self):
    NewStreamName = self.request.get('name')
    if stream.query(stream.name == NewStreamName).get() != None:
      # need to modify later to redirect to error page
      self.response.write("already exist")
    
    tag = self.request.get('tags')
    # remove white space and # sign
    tag = [x.strip()[1:] for x in tag.split(',')]
    owner = user.email()
    cover = self.request.get('cover')
    newStream = stream(name = NewStreamName, tags = tag, owner = owner, cover = cover)
    newStream.put()
    # handle subscription later here
    self.redirect('/manage')
#[END create_new_stream]

#[START upload_image]
class UploadImage(webapp2.RequestHandler):
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
class loadMore(webapp2.RequestHandler):
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
class View(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      userId = user.email()
      url = users.create_logout_url('/')
      url_linktext = 'Logout'
    else:
      self.redirect('/manage')
      return

    streamId = self.request.get("streamid")
    pageRange = self.request.get("pagerange", default_value = DEFAULT_PAGE_RANGE)
    imgUrls = []
    if streamId:
      imgUrls = getMoreImages(streamId, pageRange)
    # self.response.write(imgUrls)
    template_values = {
      'url' : url,
      'url_linktext' : url_linktext,
      'streamId' : streamId,
      'imageUrls' : imgUrls
    }
    template = JINJA_ENVIRONMENT.get_template('view.html')
    self.response.write(template.render(template_values))
#[END View]


#[START main_page]
class MainPage(webapp2.RequestHandler):
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
    
    template_values = {
      'url' : url,
      'url_linktext' : url_linktext
    }

    template = JINJA_ENVIRONMENT.get_template('index.html')
    self.response.write(template.render(template_values))
# [END main_page]

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/manage', Management),
    ('/newstream', CreateNewStream),
    ('/uploadImage', UploadImage),
    ('/view', View),
    ('/loadMore', loadMore)
], debug=True)


