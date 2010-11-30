#!/usr/bin/env python

import cgi 

from django.utils import simplejson
from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext.webapp.util import run_wsgi_app 
from selector import Selector 
from simplerepo.models import Attribute 
from simplerepo.models import AttributeValues 
from simplerepo.models import Collection 
from simplerepo.models import Item 
from simplerepo.models import ItemMetadata 
from simplerepo.models import User 
from simplerepo.template import Template
from simplerepo.utils import dirify 
from simplerepo.utils import rfc3339 
from yaro import Yaro 

#todo: figure out where this fx belongs
def check_user(req):
  user = users.get_current_user()
  if not user:
    if 'GET' == req.method:
      req.redirect(users.create_login_url(req.uri.application_uri()))
    else:
      req.redirect(req.uri.server_uri()+'/401)
  return User(user)

def get_index(req):
  user = get_current_user(req)
  t = Template(req,'index.html')
  t.assign('title','SimpleRepository') 
  req.res.body = t.fetch() 

def get_collection_form(req):
  user = get_current_user(req)
  t = Template(req,'collection_form.html')
  t.assign('collections',user.get_collections())
  t.assign('title','SimpleRepository: Collection Form') 
  req.res.body = t.fetch() 

def get_item(req):
  user = get_current_user(req)
  t = Template(req,'item.html')
  id = int(req.get('id'))
  item = Item.get_by_id(id) 
  t.assign('item',item)
  t.assign('title','SimpleRepository: Item '+str(id)) 
  req.res.body = t.fetch() 

def get_collection(req):
  user = get_current_user(req)
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
  user = get_current_user(req)
  name = req.get('name')
  if name:
    ascii_id = dirify(name)
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
  user = get_current_user(req)
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

def serve_blob(req):
  user = get_current_user(req)
  blob_key = req.get("blob_key")
  if blob_key:
    blob_info = blobstore.get(blob_key)
    if blob_info:
      if 'image/jpeg' != blob_info.content_type:
        req.res.headers['Content-Disposition'] = 'attachment; filename="'+blob_info.filename+'"' 
      req.res.headers['Content-type'] = blob_info.content_type
      req.res.headers[blobstore.BLOB_KEY_HEADER] = blob_key
      req.res.body = 'ok'

def get_hello(req):
  t = Template(req,'hello.html')
  t.assign('name',req.get('name')) 
  t.assign('title','SimpleRepository') 
  req.res.body = t.fetch() 

def get_thumbnail(req):
  blob_key = req.get("blob_key")
  width = req.get('width')
  height = req.get('height')
  if not width:
    width = 100
  if not height:
    height = 100
  if blob_key:
    blob_info = blobstore.get(blob_key)
    if blob_info:
      img = images.Image(blob_key=blob_key)
      img.resize(width=int(width), height=int(height))
      img.im_feeling_lucky()
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
  app.add('/item/{id}', GET=get_item)  
  app.add('/collection/{ascii_id}', GET=get_collection,POST=post_to_collection)  
  app.add('/hello/{name}', GET=get_hello,DELETE=delete_hello)  
  app.add('/thumbnail/{blob_key}', GET=get_thumbnail)  
  app.add('/serve/{blob_key}', GET=serve_blob)  
  app.add('/upload', POST=process_upload)  
  run_wsgi_app(app)

if __name__ == '__main__':
  main()
