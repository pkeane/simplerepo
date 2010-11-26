#!/usr/bin/env python

import cgi 
import datetime
import os
import re
import sys
import time

from django.utils import simplejson
from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext import db
from google.appengine.ext import search
from google.appengine.ext.webapp.util import run_wsgi_app 

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from yaro import Yaro 
from selector import Selector 

# Set to true if we want to have our webapp print stack traces, etc
_DEBUG = True

def _rfc3339():
  return time.strftime('%Y-%m-%dT%H:%M:%S%z')

def _dirify(str):
    str = re.sub('\&amp\;|\&', ' and ', str)
    str = re.sub('[-\s]+', '_', str)
    return re.sub('[^\w\s-]', '', str).strip().lower()

"""
queries:
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

class Template():
  def __init__(self,request,template_name):
    self.template_name = template_name
    self.request = request
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
    template_dirs.append(os.path.join(os.path.dirname(__file__), 'templates'))
    env = Environment(loader = FileSystemLoader(template_dirs))
    try:
      template = env.get_template(self.template_name)
    except TemplateNotFound:
      raise TemplateNotFound(self.template_name)
    return template.render(self.vars)

def get_user(req):
  user = users.get_current_user()
  if not user:
    if 'GET' == req.method:
      req.redirect(users.create_login_url(req.uri.application_uri()))
    else:
      #todo
      req.redirect(req.uri.application_uri()+'/401')
  return user

def get_index(req):
  user = get_user(req)
  t = Template(req,'index.html')
  t.assign('title','SimpleRepository') 
  req.res.body = t.fetch() 

def get_collection_form(req):
  user = get_user(req)
  t = Template(req,'collection_form.html')
  colls = []
  query = Collection.all()
  query.filter('created_by =',user.user_id())
  for result in query:
      colls.append(result)
  t.assign('collections',colls)
  t.assign('title','SimpleRepository: Collection Form') 
  req.res.body = t.fetch() 

def get_collection(req):
  user = get_user(req)
  t = Template(req,'collection.html')
  ascii_id = req.get('ascii_id')
  query = Collection.all()
  query.filter('ascii_id =',ascii_id)
  c = query.fetch(1)[0]
  upload_url = blobstore.create_upload_url('/upload')

  t.assign('upload_url',upload_url)
  t.assign('c',c)
  t.assign('items',c.get_items())
  t.assign('title','SimpleRepository: '+c.name) 
  req.res.body = t.fetch() 

def post_to_collection_form(req):
  user = get_user(req)
  name = req.get('name')
  if name:
    ascii_id = _dirify(name)
    collection = Collection(name=name,ascii_id=ascii_id,created_by=user.user_id())
    collection.put()
  req.redirect(req.uri.application_uri())

def post_to_collection(req):
  #creates an item
  pass

def get_401(req):
  req.res.status = '401 Unauthorized'
  req.res.body = 'unauthorized'

def process_upload(req):
  user = get_user(req)
  coll_ascii = req.form['coll_ascii']
  for key,value in req.form.items():
    if isinstance(value, cgi.FieldStorage):
      if 'blob-key' in value.type_options:
        blobinfo = blobstore.parse_blob_info(value)
        item = Item(
            coll_ascii=coll_ascii,
            created_by=user.user_id(),
            media_file_key=str(blobinfo.key()),
            media_file_mime=blobinfo.content_type,
            media_filename=blobinfo.filename)
        item.put()
  req.redirect(req.uri.server_uri()+'/collection/'+coll_ascii)

def get_hello(req):
  t = Template(req,'hello.html')
  t.assign('name',req.get('name')) 
  t.assign('title','SimpleRepository') 
  req.res.body = t.fetch() 

def get_thumbnail(req):
  blob_key = req.get("blob_key")
  if blob_key:
    blob_info = blobstore.get(blob_key)
    if blob_info:
      img = images.Image(blob_key=blob_key)
      img.resize(width=100, height=100)
      img.im_feeling_lucky()
      thumbnail = img.execute_transforms(output_encoding=images.JPEG)
      req.res.headers['Content-Type'] = 'image/jpeg'
      req.res.body = thumbnail

def get_viewitem(req):
  blob_key = req.get("blob_key")
  if blob_key:
    blob_info = blobstore.get(blob_key)
    if blob_info:
      img = images.Image(blob_key=blob_key)
      img.resize(width=640, height=600)
      #img.im_feeling_lucky()
      thumbnail = img.execute_transforms(output_encoding=images.JPEG)
      req.res.headers['Content-Type'] = 'image/jpeg'
      req.res.body = thumbnail

def delete_hello(req):
  pass

def main():
  app = Selector(wrap=Yaro)  
  app.add('401', GET=get_401)  
  app.add('', GET=get_index)  
  app.add('/', GET=get_index)  
  app.add('/collection/form', GET=get_collection_form,POST=post_to_collection_form)  
  app.add('/collection/{ascii_id}', GET=get_collection,POST=post_to_collection)  
  app.add('/hello/{name}', GET=get_hello,DELETE=delete_hello)  
  app.add('/thumbnail/{blob_key}', GET=get_thumbnail)  
  app.add('/viewitem/{blob_key}', GET=get_viewitem)  
  app.add('/upload', POST=process_upload)  
  run_wsgi_app(app)

if __name__ == '__main__':
  main()

#basic auth from
#http://appengine-cookbook.appspot.com/recipe/decorator-for-basic-http-authentication/

#import base64
#from google.appengine.ext.webapp import template
#...
#def basicAuth(func):
#  def callf(webappRequest, *args, **kwargs):
#    authHeader = webappRequest.request.headers.get('Authorization')
#    
#    if authHeader == None:
#      webappRequest.response.set_status(401, message="Authorization Required")
#      webappRequest.response.headers['WWW-Authenticate'] = 'Basic realm="Secure Area"'
#    else:
#      auth_parts = authHeader.split(' ')
#      user_pass_parts = base64.b64decode(auth_parts[1]).split(':')
#      user_arg = user_pass_parts[0]
#      pass_arg = user_pass_parts[1]
#  
#      if user_arg != "admin" or pass_arg != "foobar":
#        webappRequest.response.set_status(401, message="Authorization Required")
#        webappRequest.response.headers['WWW-Authenticate'] = 'Basic realm="Secure Area"'
#    
#        self.response.out.write(template.render('templates/error/401.html', {}))
#      else:
#        return func(webappRequest, *args, **kwargs)
#  
#  return callf

