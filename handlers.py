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

from models import *
from baseHandler import BaseHandler
from docs import *
from helper import *

from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import app_identity
from google.appengine.api import search
from google.appengine.api import mail
from google.appengine.api import images
from google.appengine.ext import blobstore
from google.appengine.api import taskqueue
from google.appengine.datastore.datastore_query import Cursor


# [END imports]

DEFAULT_STREAM_NAME = 'public stream'
DEFAULT_PAGE_RANGE = 4
# DEFAULT_KITTEN = "https://i.imgur.com/xHxXUjc.jpg"
DEFAULT_KITTEN = "/static/img/defaultkitten.jpg"
DEAFULT_LIMIT = 10

def get_stream_key(stream_name=DEFAULT_STREAM_NAME):
  return ndb.Key('stream', stream_name)

# [START management_page]
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
# [END management_page]

# [START add_to_mailing_list]
class addToMailingList(BaseHandler):
  @BaseHandler.check_log_in
  def post(self):
    frequency = int(self.request.POST.get('frequency', 0))
    logging.info(frequency)
    user = mailingListUser.query(mailingListUser.Id == users.get_current_user().email()).get()
    if not user and frequency != 0:
      new_mail_user = mailingListUser(parent = mailingUser_group(frequency), Id = users.get_current_user().email(), frequency = frequency)
      new_mail_user.put()
      self.redirect('/trending')
      return

    if user and frequency == 0:
      user.key.delete()
    elif user and user.frequency != frequency:
      user.key.delete()
      new_mail_user = mailingListUser(parent = mailingUser_group(frequency), Id = users.get_current_user().email(), frequency = frequency)
      new_mail_user.put()
    self.redirect('/trending')
# [END add_to_mailing_list]

# [START create_new_stream]
class CreateNewStream(BaseHandler):
  def sendInvitation(self, streamName, subList, sublink, optional_message = None):
    for invitee in subList:
      message = mail.EmailMessage(
        sender = 'subscription_manager@aptproj.appspotmail.com',
        subject = 'Invitation to Subscribe'
      )
      message.to = invitee
      message.body = '''You are invited to subscribe to the following stream on StreamShare!
      ''' + streamName + '''link to subscribe: ''' + sublink + '\nLog in to Subscribe!\noptional message:\n' + optional_message
      message.send()

  def post(self):
    user = users.get_current_user()
    NewStreamName = self.request.get('stream-name')
    subList = self.request.get('Subscribers')
    optional_message = self.request.get('optional-message')
    if stream.query(stream.name == NewStreamName).get() != None:
      self.redirect('/erroradd')
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
    def _tx():
      newStream.put()
      StreamDoc.createStream(str(newStream.streamID()), NewStreamName, tag)
    # atomic operation, either all added or none added!
    ndb.transaction(_tx)
    
    # send invite to subscribers
    subList = re.sub(r'[\,]+', ' ', subList).split()
    subLink = self.request.host_url + '/addsub?subscribe=' + urllib.quote(NewStreamName)
    self.sendInvitation(NewStreamName, subList, subLink, optional_message)
    self.redirect('/manage')
# [END create_new_stream]

# [START error_add]
class errorAdd(BaseHandler):
  def get(self):
    self.render_template('error.html', {})

# [END error_add]

# [START delete_stream]
class DeleteStream(BaseHandler):
  def post(self):
    user = users.get_current_user()
    streamList = self.request.POST.getall('steramToDelete')
    for curStreamName in streamList:
      if not curStreamName:
        continue
      curStreamName = urllib.unquote(curStreamName)
      try:
        curStream = stream.query(ancestor = streamGroup_key(), filters = stream.name == curStreamName).get()
      except:
        logging.exception('this stream does not exist')
      doc_id = str(curStream.streamID())
      def _tx():
        self.deleteImages(curStream.key)
        StreamDoc.removeStream(doc_id)
        curStream.delete()
      # atomic operation, either all are deleted or non deleted!
      ndb.transaction(_tx)
    self.redirect('/manage')
  
  def deleteImages(self, curStreamKey):
    # bucket_name = os.environ.get('BUCKET_NAME',
    #                           app_identity.get_default_gcs_bucket_name())
    # streamPath = '/' + bucket_name + '/' + streamId
    # cloudImages = gcs.listbucket(streamPath)
    # for img in cloudImages:
    #   try:
    #     blobkey = blobstore.create_gs_key('/gs{}'.format(img.filename))
    #     images.delete_serving_url(blobkey)
    #   except:
    #     logging.error("delete failed")
    #   try:
    #     gcs.delete(img.filename)
    #   except:
    #     logging.info('tried to delete cloud storage in local')
    # bucket_name = os.environ.get('BUCKET_NAME',
    #                            app_identity.get_default_gcs_bucket_name())
    # streamPath = '/' + bucket_name + '/' + streamId
    # cloudImages = gcs.listbucket(streamPath)
    # cloudImages = Image.query(ancestor = curStreamKey).fetch()
    # # servingUrlToDelete = []
    # for img in cloudImages:
    #   blobkey = img.gcs_key
      # try:
        # blobkey = blobstore.create_gs_key('/gs{}'.format(img.filename))
      # servingUrlToDelete.append(blobkey)
      # images.delete_serving_url(blobkey)
      # except:
        # logging.error("failed to delete serving url")
      # try:
        # gcs.delete(img.filename)
      # blobstore.delete(blobkey)
      # except:
      #   logging.info('tried to delete cloud storage in local')
      # img.key.delete()
    # try:
    #   gcs.delete(streamPath)
    # except:
    #   logging.info('tried to delete cloud storage in local')
    task = taskqueue.add(
      url='/task/deleteservingurl',
      params = {
        'streamkey' : curStreamKey.urlsafe()
      }
    )
# [END delete_stream]

# [START add_sub]
class AddSub(BaseHandler):
  @BaseHandler.check_log_in
  def get(self):
    user = users.get_current_user()
    targetStream = urllib.unquote(self.request.get('subscribe'))
    curStream = stream.query(ancestor = streamGroup_key(), filters = stream.name == targetStream).get()
    if not curStream:
      return
    
    # create a new subscribed user only not subscribed yet
    result = userSub.query(ancestor = curStream.key, filters = userSub.Id == user.email()).get()
    if not result:
      newSubUser = userSub(parent=curStream.key, Id = user.email(), subscribedStream = curStream.key)
      newSubUser.put()
    self.redirect('/view?' + urllib.urlencode({"streamid" : targetStream}))


  @BaseHandler.check_log_in
  def post(self):
    user = users.get_current_user()
    if not user:
      self.redirect(users.create_login_url('/manage'))
      return
    targetStream = urllib.unquote(self.request.get('subscribe'))
    curStream = stream.query(ancestor = streamGroup_key(), filters = stream.name == targetStream).get()
    if not curStream:
      return
    
    # create a new subscribed user only not subscribed yet
    result = userSub.query(ancestor = curStream.key, filters = userSub.Id == user.email()).get()
    if not result:
      newSubUser = userSub(parent=curStream.key, Id = user.email(), subscribedStream = curStream.key)
      newSubUser.put()

    self.redirect('/view?' + urllib.urlencode({"streamid" : targetStream}))
# [END add_sub]


# [START remove_sub]
class RemoveSub(BaseHandler):
  def post(self):
    user = users.get_current_user()
    targetStream = self.request.POST.getall('unsubscribe')
    isSingle = self.request.get('single')
    for curStream in targetStream:
      curStream = urllib.unquote(curStream)
      streamToSubscribe = stream.query(ancestor = streamGroup_key(), filters = stream.name == curStream).get()
      if not streamToSubscribe:
        continue
      result = userSub.query(ancestor = streamToSubscribe.key, filters = userSub.Id == user.email()).get()
      if result:
        result.key.delete()
    if not isSingle:
      self.redirect('/manage')
    else:
      self.redirect('/view?' + urllib.urlencode({"streamid" : urllib.unquote(targetStream[0])}))
# [END remove_sub]

# [START new_stream]
class newStream(BaseHandler):
  @BaseHandler.check_log_in
  def get(self):
    self.render_template('newstream.html', {
      'request_path' : self.request.path
    })
# [END new_stream]

# [START searchStream]
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
# [END searchStream]

# [START get_completion_index]
class getCompletionIndex(BaseHandler):
  def get(self):
    userInput = self.request.get('term')
    logging.info(userInput)
    completion_index = meta.get_meta().completion_index
    autoCompleteResult = filter(lambda x: userInput in x, completion_index)
    autoCompleteResult = sorted(autoCompleteResult)[0:20]
    self.response.headers['content-type'] = 'application/json'
    self.response.write(json.dumps(autoCompleteResult))
    

# [END get_completion_index]

class updateStream(BaseHandler):
  def get(self):
    length = self.request.get('length')
    streamName = self.request.get('streamid')
    if not streamName:
      return
    streamName = urllib.unquote(streamName)
    curStream = stream.query(ancestor = streamGroup_key(), filters = stream.name == streamName).get()
    if not curStream:
      return
    curStream.imgCount = curStream.imgCount + int(length)
    curStream.lastUploadTime = datetime.datetime.now().strftime('%m/%d/%y')
    curStream.put()

# [START upload_image]
class UploadImage(BaseHandler):
  @BaseHandler.check_log_in
  def post(self):
    uploadimages = self.request.POST.getall('file')
    streamId = self.request.get('streamid')
    unknownLoc = self.request.POST.get('unknownLoc')
    if not unknownLoc:
      lat, lon = genRandLocation()
    elif unknownLoc:
      lat, lon = genRandLocation()
    else:
      lat = self.request.POST.get('lat')
      lon = self.request.POST.get('lon')

    curStream = stream.query(ancestor = streamGroup_key(), filters = stream.name == streamId).get()
    if not curStream:
      return
    bucket_name = os.environ.get('BUCKET_NAME',
                               app_identity.get_default_gcs_bucket_name())
    write_retry_params = gcs.RetryParams(backoff_factor=1.1)

    for img in uploadimages:
      fileName = '/' + bucket_name + '/' + streamId + '/' + img.filename
      gcs_file = gcs.open(fileName, 
                          'w',
                          content_type = img.type,
                          retry_params = write_retry_params)
      gcs_file.write(img.file.read())
      gcs_file.close()
      blob_key = blobstore.create_gs_key('/gs{}'.format(fileName))
      serving_url = images.get_serving_url(blob_key, secure_url=True)
      ndb_img = Image(parent = curStream.key, serving_url = serving_url, gcs_key = blobstore.create_gs_key('/gs{}'.format(fileName)), geo =  ndb.GeoPt(lat, lon))
      ndb_img_key = ndb_img.put()
    
    # def _tx():
    #   curStream = stream.query(ancestor = streamGroup_key(), filters = stream.name == streamId).get()
    #   curStream.imgCount = curStream.imgCount + len(images)
    #   curStream.lastUploadTime = datetime.datetime.now().strftime('%m/%d/%y')
    #   curStream.put()
    # # has to be updating imagecount has to be atomic operation!
    # ndb.transaction(_tx)

# [START social]
class social(BaseHandler):
  def get(self):
    template_values = {
      'request_path' : self.request.path
    }
    self.render_template('social.html', template_values)

# [END social]

# [START get_geo_data]
class getGeoData(BaseHandler):
  def get(self):
    streamId = self.request.get('streamid')
    if not streamId:
      return
    streamId = urllib.unquote(streamId)
    curStream = stream.query(ancestor = streamGroup_key(), filters = stream.name == streamId).get()
    if not curStream:
      return
    allImages = Image.query(ancestor = curStream.key).fetch()
    imgLoc = []
    imgUrl = []
    imgTime = []
    for img in allImages:
      geo = str(img.geo)
      geo = geo.split(',')
      imgLoc.append(geo)
      imgUrl.append(images.get_serving_url(img.gcs_key))
      imgTime.append(img.addDate.isoformat())
    json_result = {
      'imgLoc' : imgLoc,
      'imgUrl' : imgUrl,
      'imgTime' : imgTime
    }
    self.response.write(json.dumps(json_result))
# [END get_geo_data]

# [START geo_view]
class geoView(BaseHandler):
  def get(self):
    streamid = self.request.get('streamid')
    self.render_template('geoview.html', {
      'streamid' : streamid
    })
# [END geo_view]

# [START get_more_images]
def getMoreImages(streamId, pageRange = DEFAULT_PAGE_RANGE, cursor = None):
  # bucket_name = os.environ.get('BUCKET_NAME',
  #                              app_identity.get_default_gcs_bucket_name())
  # streamPath = '/' +bucket_name + '/' + streamId
  # try:
  #   cloudImages = gcs.listbucket(streamPath)
  # except:
  #   return None
  # # access images by creation time
  # servingUrl = []
  # img_bucket = []
  # for img in cloudImages:
  #   img_bucket.append(img)

  # img_bucket.sort(key = lambda x : (x.st_ctime), reverse = True)
  # for i in range(marker, min(marker + pageRange, len(img_bucket))):
  #   servingUrl.append(images.get_serving_url(blobstore.create_gs_key('/gs{}'.format(img_bucket[i].filename)), secure_url = True))
  # return servingUrl
  curStream = stream.query(ancestor = streamGroup_key(), filters = stream.name == streamId).get()
  if not cursor:
    cloudImages, next_cursor, more = Image.query(ancestor = curStream.key).order(-Image.addDate).fetch_page(pageRange)
  else:
    cloudImages, next_cursor, more = Image.query(ancestor = curStream.key).order(-Image.addDate).fetch_page(pageRange, start_cursor = cursor)
  
  servingUrl = []
  for img in cloudImages:
    servingUrl.append(img.serving_url)
  return (servingUrl, next_cursor, more)

# [END get_more_images]

# [START load_more]
class loadMore(BaseHandler):
  def get(self):
    streamId = self.request.get('streamid')
    # marker = self.request.get('marker')
    cursor = Cursor(urlsafe=self.request.get('cursor'))
    imgList, next_cursor, more = getMoreImages(streamId = streamId, cursor = cursor)
    result_json = {'images' : imgList,
                    'more' : more}
    if next_cursor:
      next_cursor = next_cursor.urlsafe()
      result_json.update({'cursor' : next_cursor})
    
    # send response back as json 
    self.response.write(json.dumps(result_json))
    # streamId = self.request.get('streamid')
    # marker = self.request.get('marker')
    # imgList = getMoreImages(streamId = streamId, marker = int(marker))
    # # send response back as json 
    # self.response.write(json.dumps({'images' : imgList}))

# [END load_more]

# [START View]
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
    curStream.put()
    imgUrls = []
    if streamId:
      imgUrls, cursor, more = getMoreImages(streamId, pageRange)
      # imgUrls = getMoreImages(streamId, pageRange)
    if cursor:
      cursor = cursor.urlsafe()
    # convert more to something javascript can read
    if more:
      more = 'true'
    else:
      more = 'false'
    template_values = {
      'streamId' : streamId,
      'quotedStreamId' : urllib.quote(streamId),
      'imageUrls' : imgUrls,
      'isOwner' : isOwner,
      'isSub' : isSub,
      'cursor' : cursor,
      'more' : more
    }
    self.render_template('view.html', template_values)
# [END View]

# [START view_all]
class viewall(BaseHandler):
  def get(self):
    allStreams = stream.query(ancestor = streamGroup_key()).fetch()
    quotedStreamName = [urllib.quote(x.name) for x in allStreams]
    template_values = {
      'allstream' : allStreams,
      'quotedStreamName' : quotedStreamName,
      'request_path' : self.request.path
    }
    self.render_template('viewall.html', template_values)
# [END view_all]

# [START trending]
class Trending(BaseHandler):
  def get(self):
    trendingStream = stream.query(ancestor = streamGroup_key()).order(-stream.accessFrequency).fetch(3)
    redirect_url = ['/view?' + urllib.urlencode({'streamid': x.name}) for x in trendingStream]

    template_values = {
      'trendingStream' : trendingStream,
      'redirect_url' : redirect_url,
      'request_path' : self.request.path
    }
    self.render_template('trending.html', template_values)
# [END trending]

# [START main_page]
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