from google.appengine.ext import ndb

class stream(ndb.Model):
    name = ndb.StringProperty()
    tags = ndb.StringProperty(repeated = True)
    accessFrequency = ndb.IntegerProperty(default = 0, indexed = False)
    owner = ndb.StringProperty()
    cover = ndb.StringProperty(default = '', indexed = False)

class userSub(ndb.Model):
    Id = ndb.StringProperty()
    subscribedStream = ndb.KeyProperty(repeated = True, indexed = False)
