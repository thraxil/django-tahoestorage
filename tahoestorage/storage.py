
# Required settings:
# TAHOE_STORAGE_BASE_URL
# TAHOE_STORAGE_BASE_CAP
# TAHOE_PUBLIC_BASE_URL

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files import File
import os.path
from restclient import GET,POST
from simplejson import loads
import urllib2
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
from pprint import pprint
import itertools

class TahoeStorage(FileSystemStorage):
    def __init__(self, tahoe_base_url=settings.TAHOE_STORAGE_BASE_URL, 
                 tahoe_base_cap=settings.TAHOE_STORAGE_BASE_CAP,
                 location=None,base_url=settings.TAHOE_PUBLIC_BASE_URL):
        # make sure streaming uploader is initialized
        register_openers()

        self.tahoe_base_url = tahoe_base_url
        self.tahoe_base_cap = tahoe_base_cap
        self.base_url = base_url

    ###### Django File Storage methods to override

    def _open(self, name, mode='rb'):
        # opening read-only, so just fetch it and wrap it in File
        # could be troublesome on large files since it will keep it in memory
        # and i don't really know what to do if they try to open it for writing
        if mode != 'rb':
            raise NotImplemented
        return File(GET(self.url()))

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
        (path,fname) = os.path.split(name)
        dircap = self._dir_cap(path)
        url = self._tahoe_url(dircap)
        POST(url,params={'t':"delete",
                         'name':fname,
                         'del':"del"},
             async=False)

    def exists(self, name):
        (path,fname) = os.path.split(name)
        children = self._children(self._dir_cap(path))
        return children.has_key(fname)

    def listdir(self, path):
        children = self._children(self._dir_cap(path))
        return children.keys()

    def path(self, name):
        # no actual filesystem path so can't give this
        return None

    def size(self, name):
        cap = self._file_cap(name)
        url = settings.base_url + "file/" + urllib2.quote(cap) + "?t=json"
        info = loads(GET(url))
        return info[1]['size']

    def url(self, name):
        cap = self._file_cap(name)
        (path,fname) = os.path.split(name)
        return settings.base_url + "file/" + urllib2.quote(cap) + "/@@named=/" + urllib2.quote(fname)
    
    def get_available_name(self, name):
        if not self.exists(name):
            return name
        else:
            (path,fname) = os.path.split(name)
            (base,ext) = os.path.splitext(fname)
            # If the filename already exists, add an underscore and a number (before
            # the file extension, if one exists) to the filename until the generated
            # filename doesn't exist.
            count = itertools.count(1)
            while self.exists(name):
                # file_ext includes the dot.
                name = os.path.join(path, "%s_%s%s" % (base, count.next(), ext))

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
