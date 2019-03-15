# [START imports]
import webapp2

from handlers import *
# [END imports]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/manage', Management),
    ('/CreateNewStream', CreateNewStream),
    ('/uploadImage', UploadImage),
    ('/view', View),
    ('/loadMore', loadMore),
    ('/newstream', newStream),
    ('/search', newStream)
], debug=True)


