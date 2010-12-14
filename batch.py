#!/usr/bin/python
import getpass
import mimetypes
import os
import sys
import urllib2

GAE_PATH = "/home/pkeane/Desktop/google_appengine"
sys.path.append(GAE_PATH)
sys.path.append(GAE_PATH+"/lib/fancy_urllib")
sys.path.append(GAE_PATH+"/lib/yaml/lib")

MY_APP = 'simplerepo'

from google.appengine.tools import appengine_rpc

def encode_multipart_formdata(fields, files):
    BOUNDARY = '----------lImIt_of_THE_fIle_eW_$'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

def auth_func():
  return raw_input('Username: '), getpass.getpass('Password: ')

def get_server(app_name,auth_function):
  return appengine_rpc.HttpRpcServer(app_name+'.appspot.com',auth_function,None,'gae_login',save_cookies=True)

def get_upload_url(server,collection):
  url = server.Send('/collection/'+collection+'/upload_url',None) #None makes it GET, otherwise method is POST
  url = url.replace('https://'+MY_APP+'.appspot.com','')
  return url

def upload_file(server,filepath,collection):
  filename = os.path.basename(filepath)
  url = get_upload_url(server,collection)
  data = open(filepath).read()
  fields = []
  files = [('file',filename,data)]
  (content_type,payload) = encode_multipart_formdata(fields, files)
  resp = server.Send(url,payload=payload,content_type=content_type)
  return resp

if __name__=="__main__":
  server = get_server(MY_APP,auth_func)
  dir = '/home/pkeane/stv_histograms/img'
  for file in os.listdir(dir):
    print upload_file(server,dir+'/'+file,'new_collection')
