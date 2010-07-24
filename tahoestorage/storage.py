
# Required settings:
# TAHOE_STORAGE_BASE_URL
# TAHOE_STORAGE_BASE_CAP
# TAHOE_PUBLIC_BASE_URL

from django.db import models
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files import File
import os
import os.path
from restclient import GET,POST
from simplejson import loads
import urllib2
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
from pprint import pprint

class TahoeStorage(FileSystemStorage):
    def __init__(self, tahoe_base_url=settings.TAHOE_STORAGE_BASE_URL, 
                 tahoe_base_cap=settings.TAHOE_STORAGE_BASE_CAP,
                 location=None,base_url=None):
        # make sure streaming uploader is initialized
        register_openers()

        if location is None:
            location = settings.MEDIA_ROOT
        self.location = os.path.abspath(location)
        self.tahoe_base_url = tahoe_base_url
        self.tahoe_base_cap = tahoe_base_cap
        self.base_url = base_url

    ###### Django File Storage methods to override

    def _open(self, name, mode='rb'):
        print "_open(%s)" % name

    def _save(self, name, content):
        (path,fname) = os.path.split(name)
        dircap = self._makedirs(path)
        content.name = fname
        datagen, headers = multipart_encode({"file": content,
                                             "t" : "upload"})
        url = self._tahoe_url(dircap)
        request = urllib2.Request(url,datagen, headers)
        cap = urllib2.urlopen(request).read()
        return name

    def delete(self, name):
        print "delete(%s)" % name
        pass

    def exists(self, name):
        print "exists(%s)" % name
        pass

    def listdir(self, path):
        print "listdir(%s)" % path
#        return [key.name for key in self.bucket.list()]
        pass

    def path(self, name):
        print "path(%s)" % name
        return None

    def size(self, name):
        print "size(%s)" % name
        pass
#        return self.bucket.get_key(name).size

    def url(self, name):
        cap = self._file_cap(name)
        (path,fname) = os.path.split(name)
        return settings.TAHOE_PUBLIC_BASE_URL + "file/" + urllib2.quote(cap) + "/@@named=/" + urllib2.quote(fname)
#        return Key(self.bucket, name).generate_url(100000)
    
    def get_available_name(self, name):
        print "get_available_name(%s)" % name
        return name

    ##### "Private" methods
    def _makedirs(self,path):
        """ styled after os.makedirs, creates all the directories for the full path"""
        """ expects a rooted path like '/a/b/c' and returns the cap for 'c' """
        def md(cap,path):
            if path == "":
                return cap 
            parts = path.split("/")
            first_child = parts[0]
            rest = parts[1:]

            children = self._children(cap)
            if children.has_key(parts[0]):
                child_info = children[parts[0]]
                child_cap = child_info[1]["rw_uri"]
            else:
                child_cap = self._mkdir(cap,parts[0])

            return md(child_cap,"/".join(rest))
        return md(self.tahoe_base_cap,path)

    def _dir_cap(self,path):
        """ expects a rooted path like '/a/b/c' and returns the cap for 'c' """
        def dc(cap,path):
            if path == "":
                return cap 
            parts = path.split("/")
            first_child = parts[0]
            rest = parts[1:]

            children = self._children(cap)
            # assert child_info.has_key(child)
            child_info = children[parts[0]]
            # assert child_info[0] == "dirnode"
            child_cap = child_info[1]["rw_uri"]
            return dc(child_cap,"/".join(rest))
        return dc(self.tahoe_base_cap,path)

    def _file_cap(self,name):
        (path,fname) = os.path.split(name)
        dircap = self._dir_cap(path)
        child_info = self._children(dircap)[fname]
        return child_info[1]['ro_uri']
        

    def _json_url(self,cap):
        return self.tahoe_base_url + "uri/" + urllib2.quote(cap) + "/?t=json"

    def _tahoe_url(self,cap):
        return self.tahoe_base_url + "uri/" + urllib2.quote(cap) + "/"

    def _info(self,cap):
        return loads(GET(self._json_url(cap)))

    def _ro_cap(self,cap):
        """ get a read-only cap from a rw one """
        return self._info(cap)[1]['ro_uri']

    def _verify_cap(self,cap):
        """ get a verify cap from a rw one """
        return self._info(cap)[1]['verify_uri']

    def _mkdir(self,cap,name):
        return POST(self._tahoe_url(cap),
                    params=dict(t="mkdir",
                                name=name),
                    async=False)

    def _children(self,cap):
        return self._info(cap)[1]['children']
