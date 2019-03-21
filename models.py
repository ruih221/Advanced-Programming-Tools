from google.appengine.ext import ndb
import cloudstorage as gcs

DEFAULT_GROUP_NAME = 'dummy_group'
''' group streams together to ensure strong consistency
'''
def streamGroup_key(group_name=DEFAULT_GROUP_NAME):
    return ndb.Key('streamGroup', group_name)

def mailingUser_group(frequency=5):
    return ndb.Key('frequency', str(frequency))

# meta data class used to store completion index
class meta(ndb.Model):
    completion_index = ndb.StringProperty(repeated = True, indexed = False)

    @classmethod
    def get_meta(cls):
        meta_data = meta.get_by_id('meta')
        if not meta_data:
            meta_data = meta(id='meta')
            meta_data.put()
        return meta_data

class Image(ndb.Model):
    gcs_key = ndb.StringProperty(required = True, indexed = False)
    serving_url = ndb.StringProperty(required = True, indexed = False)
    geo = ndb.GeoPtProperty(indexed = False)
    addDate = ndb.DateTimeProperty(auto_now_add = True, required = True)

class stream(ndb.Model):
    name = ndb.StringProperty()
    tags = ndb.StringProperty(repeated = True)
    accessFrequency = ndb.IntegerProperty(default = 0)
    accessQueue = ndb.DateTimeProperty(repeated = True, indexed = False)
    imgCount = ndb.IntegerProperty(default = 0, indexed = False)
    lastUploadTime = ndb.StringProperty(indexed = False)
    owner = ndb.StringProperty()
    cover = ndb.StringProperty(default = '', indexed = False)
    
    def streamID(self):
        return self.key.id()
    
    def delete(self):
        userSubs = userSub.query(ancestor=self.key, filters = userSub.subscribedStream == self.key)
        for users in userSubs:
            users.key.delete()
        self.key.delete()

class userSub(ndb.Model):
    Id = ndb.StringProperty()
    subscribedStream = ndb.KeyProperty()


# class userSub(ndb.Model):
#     Id = ndb.StringProperty()
#     subscribedStream = ndb.KeyProperty(repeated = True, indexed = False)

#     def removeSub(self, key):
#         self.subscribedStream.remove(key)
    
#     def addSub(self, key):
#         self.subscribedStream.append(key)

class mailingListUser(ndb.Model):
    Id = ndb.StringProperty()
    frequency = ndb.IntegerProperty(indexed=False, default = 5)