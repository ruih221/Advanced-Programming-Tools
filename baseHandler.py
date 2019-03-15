# [START imports]
import jinja2
import webapp2
import logging

import os

from google.appengine.api import users
from models import stream, userSub
# [END imports]

template_dir = os.path.join(os.path.dirname(__file__), 'templates')

JINJA_ENVIRONMENT = jinja2.Environment(
  loader=jinja2.FileSystemLoader(template_dir),
  extensions=['jinja2.ext.autoescape'],
  autoescape=True
)

#[START base]
class BaseHandler(webapp2.RequestHandler):
  """ include some helper functions for all other handlers """
  @classmethod
  def check_log_in(self, handler):
    def check_user(self, *args, **kwargs):
      user = users.get_current_user()
      if user:
        # create user subscription if not already created 
        subscribedStream = userSub.query(userSub.Id == user.email()).get()
        if subscribedStream == None:
          sub = userSub(Id = user.email(), subscribedStream = [])
          sub.put()
        # call handlers
        handler(self, *args, **kwargs)
      else:
        self.redirect("/")
        return
    return check_user

  def render_template(self, filename, template_values):
    template_values.update(self.generateLoggingInfo())
    template = JINJA_ENVIRONMENT.get_template(filename)
    self.response.write(template.render(template_values))

  def generateLoggingInfo(self):
    if (users.get_current_user()):
      url = users.create_logout_url('/')
      url_linktext = 'Logout'
    else:
      url = users.create_login_url(self.request.uri)
      url_linktext = 'Login'
    return {
      'url' : url,
      'url_linktext': url_linktext
    }
#[END base]