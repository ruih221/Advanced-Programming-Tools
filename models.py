from google.appengine.ext import ndb
import cloudstorage as gcs

class stream(ndb.Model):
    name = ndb.StringProperty()
    tags = ndb.StringProperty(repeated = True)
    accessFrequency = ndb.IntegerProperty(default = 0)
    accessQueue = ndb.DateTimeProperty(repeated = True, indexed = False)
    owner = ndb.StringProperty()
    cover = ndb.StringProperty(default = '', indexed = False)
    
    def streamID(self):
        return self.key.id()
    
    def delete(self):
        userSubs = userSub.query(userSub.subscribedStream.IN(self.key))
        for users in userSubs:
            users.subscribedStream.remove(self.key)
        self.key.delete()

class userSub(ndb.Model):
    Id = ndb.StringProperty()
    subscribedStream = ndb.KeyProperty(repeated = True, indexed = False)

    def removeSub(self, key):
        self.subscribedStream.remove(key)
    
    def addSub(self, key):
        self.subscribedStream.append(key)

class mailingListUser(ndb.Model):
    Id = ndb.StringProperty()
    frequency = ndb.IntegerProperty(indexed=False, default = 5)