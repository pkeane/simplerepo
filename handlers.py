#!/usr/bin/env python

import cgi 
import os

from django.utils import simplejson
from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext.webapp.util import run_wsgi_app 
from selector import Selector 
from simplerepo import Attribute 
from simplerepo import AttributeValues 
from simplerepo import Dropbox 
from simplerepo import Item 
from simplerepo import ItemMetadata 
from simplerepo import Note 
from simplerepo import Template
from simplerepo import dirify 
from simplerepo import rfc3339 
from simplerepo import get_data 
import urlparse
from yaro import Yaro 

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'templates')

def get_index(req):
  user = users.get_current_user()
  if not user:
      return req.redirect(users.create_login_url(req.uri.application_uri()))
  t = Template(req,'index.html',TEMPLATE_PATH)
  upload_url = blobstore.create_upload_url('/upload')
  t.assign('upload_url',upload_url)
  query = Item.all()
  items = query.fetch(1000)
  t.assign('items',items)
  t.assign('title','SimpleRepository: Items') 
  req.res.body = t.fetch() 

def get_item(req):
  user = users.get_current_user()
  if not user:
      return req.redirect(users.create_login_url(req.uri.application_uri()))
  t = Template(req,'item.html',TEMPLATE_PATH)
  id = int(req.get('id'))
  item = Item.get_by_id(id) 
  t.assign('item',item)
  t.assign('title','SimpleRepository: Item '+str(id)) 
  req.res.body = t.fetch() 

def get_attributes(req):
  user = users.get_current_user()
  if not user:
      return req.redirect(users.create_login_url(req.uri.application_uri()))
  t = Template(req,'attributes.html',TEMPLATE_PATH)
  query = Attribute.all()
  atts = query.fetch(1000)
  t.assign('attributes',atts)
  t.assign('title','SimpleRepository: Attributes') 
  req.res.body = t.fetch() 

def get_notes(req):
  user = users.get_current_user()
  if not user:
      return req.redirect(users.create_login_url(req.uri.application_uri()))
  t = Template(req,'notes.html',TEMPLATE_PATH)
  t.assign('title','SimpleRepository: Notes') 
  t.assign('notes',Note.get_list_by_user(user))
  req.res.body = t.fetch() 

def get_dropbox(req):
  user = users.get_current_user()
  if not user:
      return req.redirect(users.create_login_url(req.uri.application_uri()))
  t = Template(req,'dropbox.html',TEMPLATE_PATH)
  t.assign('title','SimpleRepository: Dropbox') 
  t.assign('dropbox_items',Dropbox.get_list_by_user(user))
  req.res.body = t.fetch() 

def get_dropbox_item(req):
  user = users.get_current_user()
  if not user:
      return req.redirect(users.create_login_url(req.uri.application_uri()))
  id = int(req.get('id'))
  dropbox_item = Dropbox.get_by_id(id) 
  req.res.headers['Content-Type'] = dropbox_item.mime_type
  req.res.body = dropbox_item.data 

def get_items_json(req):
    pass

def get_upload_url(req):
  user = users.get_current_user()
  if not user:
      return req.redirect(users.create_login_url(req.uri.application_uri()))
  upload_url = blobstore.create_upload_url('/upload')
  req.res.body = upload_url 

def get_attribute(req):
  user = users.get_current_user()
  if not user:
      return req.redirect(users.create_login_url(req.uri.application_uri()))
  t = Template(req,'attribute.html',TEMPLATE_PATH)
  ascii_id = req.get('ascii_id')
  query = Attribute.all()
  query.filter('ascii_id =',ascii_id)
  att = query.fetch(1)[0]
  t.assign('att',att)
  req.res.body = t.fetch() 

def delete_attribute(req):
  user = users.get_current_user()
  if not user:
      return req.redirect(users.create_login_url(req.uri.application_uri()))
  ascii_id = req.get('ascii_id')
  query = Attribute.all()
  query.filter('ascii_id =',ascii_id)
  att = query.fetch(1)[0]
  #full delete???
  att.delete()

def post_to_dropbox(req):
  user = users.get_current_user()
  note = req.get('note')
  url = req.get('url')
  try:
    (mime_type,data,title) = get_data(url)
  except:
    req.res.body = 'sorry, could not ingest '+url
    return
  dbox = Dropbox( url=url,note=note,owner=user.user_id(),mime_type=mime_type,data=data,title=title)
  dbox.put()
  return req.redirect(req.uri.server_uri()+'/dropbox')

def post_to_notes(req):
  user = users.get_current_user()
  if not user:
      return req.redirect(users.create_login_url(req.uri.application_uri()))
  text = req.get('text')
  note = Note(owner=user.user_id(),text=text)
  note.put()
  return req.redirect(req.uri.server_uri()+'/notes')

def delete_note(req):
  user = users.get_current_user()
  if not user:
      return req.redirect(users.create_login_url(req.uri.application_uri()))
  id = int(req.get('id'))
  note = Note.get_by_id(id) 
  note.delete()
  return req.redirect(req.uri.server_uri()+'/notes')

def post_to_attributes(req):
  user = users.get_current_user()
  if not user:
      return req.redirect(users.create_login_url(req.uri.application_uri()))
  name = req.get('name')
  if name:
    ascii_id = dirify(name)
    if Attribute.exists(ascii_id):
      return req.redirect(req.uri.application_uri())
    att = Attribute(name=name,ascii_id=ascii_id,values_count=0)
    att.put()
  return req.redirect(req.uri.application_uri())

def get_401(req):
  req.res.status = '401 Unauthorized'
  req.res.body = 'unauthorized'

def process_upload(req):
  user = users.get_current_user()
  filename = ''
  for key,value in req.form.items():
    if isinstance(value, cgi.FieldStorage):
      if 'blob-key' in value.type_options:
        blobinfo = blobstore.parse_blob_info(value)
        filename = blobinfo.filename
        item = Item(
            coll_ascii=coll_ascii,
            created_by=user_id,
            media_file_key=str(blobinfo.key()),
            media_file_mime=blobinfo.content_type,
            media_filename=blobinfo.filename)
        item.put()
  req.res.body = 'uploaded '+filename 

def process_formupload(req):
  for key,value in req.form.items():
    if isinstance(value, cgi.FieldStorage):
      if 'blob-key' in value.type_options:
        blobinfo = blobstore.parse_blob_info(value)
        item = Item(
            created_by=user.user_id(),
            coll_ascii=coll_ascii,
            created_by=user_id,
            media_file_key=str(blobinfo.key()),
            media_file_mime=blobinfo.content_type,
            media_filename=blobinfo.filename)
        item.put()
  return req.redirect(req.uri.server_uri())

def serve_blob(req):
  blob_key = req.get("blob_key")
  if blob_key:
    blob_info = blobstore.get(blob_key)
    if blob_info:
      if 'image/jpeg' != blob_info.content_type:
        req.res.headers['Content-Disposition'] = 'attachment; filename="'+blob_info.filename+'"' 
      req.res.headers['Content-type'] = blob_info.content_type
      req.res.headers[blobstore.BLOB_KEY_HEADER] = blob_key
      req.res.body = 'ok'

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

def main():
  app = Selector(wrap=Yaro)  
  app.add('401', GET=get_401)  
  app.add('', GET=get_index)  
  app.add('/', GET=get_index)  
  app.add('/items.json', GET=get_items_json)  
  app.add('/items', GET=get_item)  
  app.add('/item/{id}', GET=get_item)  
  app.add('/dropbox', POST=post_to_dropbox,GET=get_dropbox)  
  app.add('/notes', POST=post_to_notes,GET=get_notes)  
  app.add('/note/{id}', DELETE=delete_note)  
  app.add('/dropbox/{id}', GET=get_dropbox_item)  
  app.add('/thumbnail/{blob_key}', GET=get_thumbnail)  
  app.add('/serve/{blob_key}', GET=serve_blob)  
  app.add('/attributes', GET=get_attributes,POST=post_to_attributes)  
  app.add('/attribute/{ascii_id}', GET=get_attribute,DELETE=delete_attribute)  
  app.add('/upload', POST=process_upload)  
  app.add('/upload_url', GET=get_upload_url)  
  run_wsgi_app(app)

if __name__ == '__main__':
  main()
