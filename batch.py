#!/usr/bin/python
import getpass
import mimetypes
import sys
import urllib2

sys.path.append("/home/pkeane/Desktop/google_appengine")
sys.path.append("/home/pkeane/Desktop/google_appengine/lib/fancy_urllib")

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

server = appengine_rpc.HttpRpcServer('simplerepo.appspot.com',auth_func,None,'gae_login',save_cookies=True)

url = server.Send('/collection/new_collection/upload_url',None) #None makes it GET, otherwise method is POST

url = url.replace('https://simplerepo.appspot.com','')

data = open('redbox.jpg').read()
#data = open('pic.jpg').read()


fields = []
files = [('file','redbox.jpg',data)]
#files = [('file','pic.jpg',data)]

print "posting image"

(content_type,payload) = encode_multipart_formdata(fields, files)

#server.opener.add_handler(urllib2.HTTPRedirectHandler())
server.Send(url,payload=payload,content_type=content_type)
