# [START imports]
import webapp2

import re

from handlers import *
from taskHandler import *
# [END imports]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/manage', Management),
    ('/CreateNewStream', CreateNewStream),
    ('/uploadImage', UploadImage),
    ('/view', View),
    ('/viewall', viewall),
    ('/loadMore', loadMore),
    ('/newstream', newStream),
    ('/erroradd', errorAdd),
    ('/search', searchStream),
    ('/addtomailing', addToMailingList),
    ('/trending', Trending),
    ('/addsub', AddSub),
    ('/removesub', RemoveSub),
    ('/deletestream', DeleteStream),
    ('/task/updateLeaderBoard', updateLeaderboard),
    (r'/task/senddigest\d+', senddigest)
], debug=True)


