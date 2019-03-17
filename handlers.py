# [START imports]
import cgi
import webapp2
import cloudstorage as gcs

import os
import logging
import urllib
from urlparse import urlparse
import json
import re
import datetime

from models import stream, userSub, streamGroup_key
from baseHandler import BaseHandler
from docs import *

from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import app_identity
from google.appengine.api import search
from google.appengine.api import mail
from google.appengine.api import images
from google.appengine.ext import blobstore
# [END imports]

DEFAULT_STREAM_NAME = 'public stream'
DEFAULT_PAGE_RANGE = 4
DEFAULT_KITTEN = 'https://storage.googleapis.com/aptproj.appspot.com/defaultkitten.jpg'
DEAFULT_LIMIT = 10

def get_stream_key(stream_name=DEFAULT_STREAM_NAME):
  return ndb.Key('stream', stream_name)

#[START management_page]
class Management(BaseHandler):
  @BaseHandler.check_log_in
  def get(self):
    user = users.get_current_user()
    allStreams = stream.query(ancestor = streamGroup_key()).fetch()
    subscribedStream = []
    quotedSubName = []
    for curStream in allStreams:
      if userSub.query(ancestor = curStream.key, filters = userSub.Id == user.email()).get():
        subscribedStream.append(curStream)
        quotedSubName.append(urllib.quote(curStream.name))
    ownedStream = stream.query(ancestor = streamGroup_key(), filters = stream.owner == user.email())
    quotedName = [urllib.quote(x.name) for x in ownedStream]
    self.render_template('management.html', {
      'request_path' : self.request.path,
      'ownedStream' : ownedStream,
      'subscribedStream' : subscribedStream,
      'quotedName' : quotedName,
      'quotedSubName' : quotedSubName
    })
#[END management_page]

#[START create_new_stream]
class CreateNewStream(BaseHandler):
  def post(self):
    user = users.get_current_user()
    NewStreamName = self.request.get('stream-name')
    if stream.query(stream.name == NewStreamName).get() != None:
      # need to modify later to redirect to error page
      return
    
    tag = self.request.get('tags')
    # remove white space and # sign
    tag = re.sub(r'#', ' ', tag)
    tag = re.sub(r'[\,\.]+', ' ', tag).lower()
    tag = tag.split()
    owner = user.email()
    cover = self.request.get('cover')
    if not cover:
      cover = DEFAULT_KITTEN
    newStream = stream(parent = streamGroup_key(), name = NewStreamName, tags = tag, owner = owner, cover = cover)
    newStream.put()
    StreamDoc.createStream(str(newStream.streamID()), NewStreamName, tag)
    # handle subscription later here
    self.redirect('/newstream')
#[END create_new_stream]

#[START delete_stream]
class DeleteStream(BaseHandler):
  def post(self):
    user = users.get_current_user()
    streamList = self.request.POST.getall('steramToDelete')
    for curStreamName in streamList:
      if not curStreamName:
        continue
      self.deleteImages(curStreamName)
      curStream = stream.query(stream.name == curStreamName).get()
      doc_id = str(curStream.streamID())
      def _tx():
        StreamDoc.removeStream(doc_id)
        curStream.delete()
      ndb.transaction(_tx)
    logging.info(streamList)
    self.redirect('/manage')
  
  def deleteImages(self, streamId):
    bucket_name = os.environ.get('BUCKET_NAME',
                               app_identity.get_default_gcs_bucket_name())
    streamPath = '/' + bucket_name + '/' + streamId
    cloudImages = gcs.listbucket(streamPath)
    for img in cloudImages:
      try:
        blobkey = blobstore.create_gs_key('/gs{}'.format(img.filename))
        logging.info(blobkey)
        images.delete_serving_url(blobkey)
      except:
        return
      try:
        gcs.delete(img.filename)
      except:
        logging.info('tried to delete cloud storage in local')
    try:
      gcs.delete(streamPath)
    except:
      logging.info('tried to delete cloud storage in local')


    

#[END delete_stream]

#[START add_sub]
class AddSub(BaseHandler):
  def post(self):
    user = users.get_current_user()
    if not user:
      self.redirect(create_login_url('/manage'))
      return
    targetStream = self.request.get('subscribe')
    curStream = stream.query(stream.name == targetStream).get()
    if not curStream:
      return
    
    # create a new subscribed user only not subscribed yet
    result = userSub.query(ancestor = curStream.key, filters = userSub.Id == user.email()).get()
    if not result:
      newSubUser = userSub(parent=curStream.key, Id = user.email(), subscribedStream = curStream.key)
      newSubUser.put()

    self.redirect('/view?' + urllib.urlencode({"streamid" : targetStream}))
#[END add_sub]


#[START remove_sub]
class RemoveSub(BaseHandler):
  def post(self):
    user = users.get_current_user()
    targetStream = self.request.POST.getall('unsubscribe')
    isSingle = self.request.get('single')
    for curStream in targetStream:
      streamToSubscribe = stream.query(ancestor = streamGroup_key(), filters = stream.name == curStream).get()
      if not streamToSubscribe:
        continue
      result = userSub.query(ancestor = streamToSubscribe.key, filters = userSub.Id == user.email()).get()
      if result:
        result.key.delete()
    if not isSingle:
      self.redirect('/manage')
    else:
      self.redirect('/view?' + urllib.urlencode({"streamid" : targetStream[0]}))
#[END remove_sub]

#[START new_stream]
class newStream(BaseHandler):
  @BaseHandler.check_log_in
  def get(self):
    self.render_template('newstream.html', {
      'request_path' : self.request.path
    })
#[END new_stream]

#[START searchStream]
class searchStream(BaseHandler):
  @BaseHandler.check_log_in 
  def get(self):
    query = self.request.get('query')
    result_len = 0
    if query:
      try:
        # sort by relevance, display top 10 results
        sortopt = search.SortOptions(match_scorer=search.MatchScorer())
        search_query = search.Query(
          query_string = query.strip(),
          options = search.QueryOptions(
            offset = 0,
            sort_options=sortopt
          )
        )
        search_results = StreamDoc.getIndex().search(search_query)
        result_len = search_results.number_found
      except search.Error:
        logging.info('search error')
        return
    
    result = []
    redirect_url = []
        
    # id = str(stream.query(stream.name=='cat').get().streamID())
    # logging.info(id)
    # doc = StreamDoc.getDocById(id)
    # logging.info(doc.field('name').value)

    if result_len:
      for doc in search_results:
        # create document manager to access helper method 
        curDoc = StreamDoc(doc)
        streamId = curDoc.getStreamName()
        targetStream = stream.query(stream.name == streamId).get()
        if targetStream:
          result.append(targetStream)
      redirect_url = ['/view?' + urllib.urlencode({'streamid': x.name}) for x in result]
    template_values = {
      'number_found' : len(result),
      'search_result' : result,
      'redirect_url' : redirect_url,
      'searchText': query,
      'request_path' : self.request.path
    }
    self.render_template('search.html', template_values)
#[END searchStream]

#[START upload_image]
class UploadImage(BaseHandler):
  @BaseHandler.check_log_in
  def post(self):
    images = self.request.POST.getall('file')
    streamId = self.request.get('streamid')
    curStream = stream.query(stream.name == streamId)
    if not curStream:
      return
    bucket_name = os.environ.get('BUCKET_NAME',
                               app_identity.get_default_gcs_bucket_name())
    write_retry_params = gcs.RetryParams(backoff_factor=1.1)
    #TODO add duplicate detection
    for img in images:
      fileName = '/' + bucket_name + '/' + streamId + '/' + img.filename
      gcs_file = gcs.open(fileName, 
                          'w',
                          content_type = img.type,
                          retry_params = write_retry_params)
      gcs_file.write(img.file.read())
      gcs_file.close()
    # update uplaod time and image count
    curStream.imgCount += len(images)
    curStream.lastUploadTime = datetime.datetime.now().strftime('%m/%d/%y')
    
#[END upload_image]

#[START get_more_images]
def getMoreImages(streamId, pageRange = DEFAULT_PAGE_RANGE, marker=0):
  bucket_name = os.environ.get('BUCKET_NAME',
                               app_identity.get_default_gcs_bucket_name())
  streamPath = '/' +bucket_name + '/' + streamId
  try:
    cloudImages = gcs.listbucket(streamPath)
  except:
    return None
  # access images by creation time
  servingUrl = []
  img_bucket = []
  for img in cloudImages:
    img_bucket.append(img)

  img_bucket.sort(key = lambda x : (x.st_ctime), reverse = True)
  for i in range(marker, min(marker + pageRange, len(img_bucket))):
    servingUrl.append(images.get_serving_url(blobstore.create_gs_key('/gs{}'.format(img_bucket[i].filename))))

  return servingUrl
#[END get_more_images]

#[START load_more]
class loadMore(BaseHandler):
  def get(self):
    streamId = self.request.get('streamid')
    marker = self.request.get('marker')
    imgList = getMoreImages(streamId = streamId, marker = int(marker))
    # send response back as json 
    self.response.write(json.dumps({'images' : imgList}))

#[END load_more]

#[START View]
class View(BaseHandler):
  def get(self):
    streamId = self.request.get("streamid")
    pageRange = self.request.get("pagerange", DEFAULT_PAGE_RANGE)
    curStream = stream.query(ancestor = streamGroup_key(), filters = stream.name == streamId).get()
    if not curStream:
      # redirect if stream doesn't exist
      self.redirect('/')
      return
    # check if user if the owner or subscriber
    user = users.get_current_user()
    if user:
      isOwner = user.email() == curStream.owner
      isSub = False
      if userSub.query(ancestor = curStream.key, filters = userSub.Id == user.email()).get():
        isSub = True
    else:
      isOwner = False
      isSub = False
    # increment access frequency and update accessQueue
    curStream.accessFrequency += 1
    curStream.accessQueue.append(datetime.datetime.now())
    imgUrls = []
    if streamId:
      imgUrls = getMoreImages(streamId, pageRange)
    template_values = {
      'streamId' : streamId,
      'imageUrls' : imgUrls,
      'isOwner' : isOwner,
      'isSub' : isSub
    }
    self.render_template('view.html', template_values)
#[END View]

class Trending(BaseHandler):
  @BaseHandler.check_log_in
  def get(self):
    trendingStream = stream.query().order(-stream.accessFrequency).fetch(3)
    redirect_url = ['/view?' + urllib.urlencode({'streamid': x.name}) for x in trendingStream]

    template_values = {
      'trendingStream' : trendingStream,
      'redirect_url' : redirect_url
    }
    self.render_template('trending.html', template_values)


class addToMailingList(BaseHandler):
  def post(self):
    frequency = self.request.POST.get('frequency', 0)
    user = mailingListUser.query(mailingListUser.Id == users.get_current_user())
    if not user:
      user = mailingListUser(Id = users.get_curernt_user().email())
      user.put()
    if frequency == 0:
      user.delete()
    else:
      user.frequency = frequency


#[START main_page]
class MainPage(BaseHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      self.redirect('manage')
      # subscribedStream = userSub.query(userSub.Id == user.email()).get()

      # # create user subscription if not already created 
      # if subscribedStream == None:
      #   sub = userSub(Id = user.email(), subscribedStream = [])
      #   sub.put()
      return
    else:
      url = users.create_login_url(self.request.uri)
      url_linktext = 'Login with Google'
      
    self.render_template('index.html', {})
# [END main_page]