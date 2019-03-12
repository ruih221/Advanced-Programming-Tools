# [START imports]
import cgi
import jinja2
import webapp2

import os
import urllib

from models import stream, userSub

from google.appengine.ext import ndb
from google.appengine.api import users

JINJA_ENVIRONMENT = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
  extensions=['jinja2.ext.autoescape'],
  autoescape=True
)

# [END imports]


DEFAULT_STREAM_NAME='public stream'
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

#[START main_page]
class MainPage(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      self.redirect('manage')
      subscribedStream = userSub.query(userSub.Id == user.email()).get()

      # create user subscription if not already created 
      if subscribedStream != None:
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
    ('/newstream', CreateNewStream)
], debug=True)


