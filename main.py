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
    ('/updateStream', updateStream),
    ('/view', View),
    ('/viewall', viewall),
    ('/loadMore', loadMore),
    ('/newstream', newStream),
    ('/erroradd', errorAdd),
    ('/social', social),
    ('/search', searchStream),
    ('/getCompletionIndex', getCompletionIndex),
    ('/addtomailing', addToMailingList),
    ('/trending', Trending),
    ('/geoview', geoView),
    ('/getGeoData', getGeoData),
    ('/addsub', AddSub),
    ('/removesub', RemoveSub),
    ('/deletestream', DeleteStream),
    ('/task/updateLeaderBoard', updateLeaderboard),
    ('/task/rebuildCompletionIndex', rebuildCompletionIndex),
    (r'/task/senddigest\d+', senddigest)
], debug=False)


