from django.utils import simplejson
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import search
from google.appengine.api import urlfetch
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import os
import re
import time

def rfc3339():
  return time.strftime('%Y-%m-%dT%H:%M:%S%z')

def dirify(str):
    str = re.sub('\&amp\;|\&', ' and ', str)
    str = re.sub('[-\s]+', '_', str)
    return re.sub('[^\w\s-]', '', str).strip().lower()

def get_data(url):
  result = urlfetch.fetch(url=url)
  mime_type = result.headers['Content-Type']
  return (mime_type,result.content)

class Template():
  def __init__(self,request,template_name,template_path):
    self.template_name = template_name
    self.request = request
    self.template_path = template_path
    self.vars = {}

  def assign(self,key,val):
    self.vars[key] = val

  def fetch(self):
    values = {
      'request': self.request,
      'user': users.GetCurrentUser(),
      'login_url': users.CreateLoginURL(self.request.uri.application_uri()),
      'logout_url': users.CreateLogoutURL(self.request.uri.server_uri() + '/'),
      'debug': self.request.get('deb'), 
      'application_name': 'SimpleRepository',
    }
    self.vars.update(values)
    template_dirs = []
    #template_dirs.append(os.path.join(os.path.dirname(__file__), 'templates'))
    template_dirs.append(self.template_path)
    env = Environment(loader = FileSystemLoader(template_dirs))
    try:
      template = env.get_template(self.template_name)
    except TemplateNotFound:
      raise TemplateNotFound(self.template_name)
    return template.render(self.vars)

"""
queries needed:
  - get list of attributes and values count by collection
  - get list of values and occurrrences count by attribute
  - get set of items for given att-val
  - get set of items for a free text search
  - get hit count (items) for a free text search per collection
"""

class Collection(db.Model):
  name = db.StringProperty(required=True)
  ascii_id = db.StringProperty(required=True)
  created = db.DateTimeProperty(auto_now_add=True)
  created_by = db.StringProperty(required=True) 
  attributes = db.ListProperty(db.Key)

  def get_items(self):
      items = []
      query = Item.all()
      query.filter('coll_ascii =',self.ascii_id)
      query.order('-created')
      for result in query:
          items.append(result)
      return items

  def get_items_count(self):
      query = Items.all()
      query.filter('coll_ascii_id =',self.ascii_id)
      return query.count() 
 
  @classmethod
  def get_list_by_user(self,user):
    colls = []
    query = Collection.all()
    query.filter('created_by =',user.user_id())
    for result in query:
      colls.append(result)
    return colls


#allows us to get collection's list of attributes
class Attribute(db.Model):
  name = db.StringProperty(required=True)
  ascii_id = db.StringProperty(required=True)
  coll_ascii = db.StringProperty(required=True)
  values_count = db.IntegerProperty(indexed=False)

#when putting, pass in an attribute as parent
#grab all values for an attribute by using ANCESTOR_IS clause
#http://code.google.com/appengine/docs/python/datastore/gqlreference.html
class AttributeValues(db.Model):
  values = db.StringListProperty(required=True)

class Item(search.SearchableModel):
  coll_ascii = db.StringProperty(required=True)
  status = db.StringProperty(required=True,default='public',choices=['public','draft','delete','archived'])
  created = db.DateTimeProperty(auto_now_add=True)
  created_by = db.StringProperty(required=True) 
  updated = db.DateTimeProperty(auto_now=True)
  #media_file = blobstore.BlobReferenceProperty()
  thumbnail_link = db.StringProperty() 
  media_file_key = db.StringProperty() 
  media_filename = db.StringProperty() 
  media_file_mime = db.StringProperty()
  json_doc = db.TextProperty(required=False,indexed=False)
  #allows full-text search
  search_text = db.TextProperty()

  def put(self):
    super_type = self.media_file_mime.split('/')[0]
    if 'image' == super_type:
      self.thumbnail_link = '/thumbnail/'+self.media_file_key
    else:
      if 'application/pdf' == self.media_file_mime:
        self.thumbnail_link = '/www/images/pdf.jpg'
      else:
        self.thumbnail_link = '/www/images/'+super_type+'.jpg'
    return db.Model.put(self)

  @classmethod
  def SearchableProperties(cls):
    return [['search_text']]

#when putting, pass in an item as parent
class ItemMetadata(db.Model):
  #allows search by exact att-val
  #format as <coll_ascii_id>.<att_ascii_id>:<value_text>
  metadata = db.StringListProperty()

class Dropbox(db.Model):
  url = db.StringProperty(required=True)
  owner = db.StringProperty(required=True) 
  mime_type = db.StringProperty()
  data = db.BlobProperty()
  created = db.DateTimeProperty(auto_now_add=True)

  @classmethod
  def get_list_by_user(self,user):
    dropbox_items = []
    query = Dropbox.all()
    query.filter('owner =',user.user_id())
    for result in query:
      dropbox_items.append(result)
    return dropbox_items 


