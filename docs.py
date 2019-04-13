''' Implemented the search functionality based on app engine serach code sample
https://github.com/GoogleCloudPlatform/appengine-search-python-java/tree/master/python
'''
#[START imports]
import logging

from models import stream, userSub

from google.appengine.api import search
from google.appengine.ext import ndb
#[END imports]

class BaseDocumentManager(object):
    ''' provide helper methods for document access '''
    INDEX_NAME = None
    
    def __init__(self, doc):
        self.doc = doc

    def getFieldValue(self, name):
        try:
            return self.doc.field(name).value
        except ValueError:
            return None
    
    @classmethod
    def getIndex(cls):
        return search.Index(name = cls.INDEX_NAME)
    
    @classmethod
    def add(cls, docs):
        try:
            return cls.getIndex().put(docs)
        except search.Error:
            logging.exception("error adding documents")

    @classmethod
    def removeDoc(cls, doc_id):
        if not doc_id:
            return
        try:
            cls.getIndex().delete(doc_id)
        except search.Error:
            logging.exception('failed to delete {} in removeDoc'.format(doc_id))

    @classmethod
    def getDoc(cls, doc_id):
        if not doc_id:
            return None
        try:
            index = cls.getIndex()
            return index.get(doc_id)
        except search.InvalidReuqest:
            return None

class ImgDoc(BaseDocumentManager):
    INDEX_NAME = "Imgs0"

    IMG_URL = "url"
    IMG_STREAM = "stream"
    IMG_GEO = "img_location"

    def getImgUrl(self):
        return self.getFieldValue(self.IMG_URL)

    def getImgStream(self):
        return self.getFieldValue(self.IMG_STREAM)

    @classmethod
    def getDocById(cls, id):
        return cls.getDoc(id)
    
    @classmethod
    def removeImg(cls, doc_id):
        cls.removeDoc(doc_id)
    
    @classmethod
    def createStream(
        cls, ImgId = None, streamName = None, IMG_URL = None, GeoPoint = None
    ):
        docField = [
            search.TextField(name=cls.IMG_URL, value=IMG_URL),
            search.TextField(name=cls.IMG_STREAM, value=streamName),
            search.GeoField(name=cls.IMG_GEO, value=GeoPoint)
        ]
        doc = search.Document(doc_id=ImgId, fields=docField)
        ImgDoc.add(doc)

class StreamDoc(BaseDocumentManager):
    INDEX_NAME = 'Streams0'

    STREAM_name = 'name'
    STREAM_TAGS = 'tags'

    def getStreamName(self):
        return self.getFieldValue(self.STREAM_name)

    @classmethod
    def getDocById(cls, id):
        return cls.getDoc(id)
    
    @classmethod
    def removeStream(cls, doc_id):
        cls.removeDoc(doc_id)
    
    @classmethod
    def createStream(
        cls, streamId = None, streamName = None, streamTags = None
    ):
        docField = [
            search.TextField(name=cls.STREAM_name, value=streamName),
            search.TextField(name=cls.STREAM_TAGS, value=','.join(streamTags))
        ]
        doc = search.Document(doc_id=streamId, fields=docField)
        StreamDoc.add(doc)
    
