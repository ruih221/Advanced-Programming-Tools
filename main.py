# [START imports]
import webapp2

from handlers import *
from taskHandler import *
# [END imports]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/manage', Management),
    ('/CreateNewStream', CreateNewStream),
    ('/uploadImage', UploadImage),
    ('/view', View),
    ('/loadMore', loadMore),
    ('/newstream', newStream),
    ('/search', searchStream),
    ('/addtomailing', addToMailingList),
    ('/trending', Trending),
    ('/task/updateLeaderBoard', updateLeaderboard),
    ('/task/senddigest(\d+)', senddigest)
], debug=True)


