Let's you use a Tahoe Grid as the storage backend for a Django
FileField. 

It would look something like this (in your apps' models.py):


    from tahoestorage.storage import TahoeStorage
    ts = TahoeStorage()
    
    class Whatever(models.Model):
        file = models.FileField(upload_to='a/b/c/', storage=ts)

This expects a certain configuration though. You (obviously) need to
have a Tahoe grid running. In your settings, you will then need to
set:

TAHOE_STORAGE_BASE_URL

The base URL for accessing your grid. 
Probably something like "http://localhost:3456/"

A localhost URL is recommended, which means you need to run a Tahoe
Node (it doesn't have to be a storage node) on the same machine as
your Django app is running on.

TAHOE_STORAGE_BASE_CAP

A R/W directory CAP to use as the "root" of your django
storage. You'll want to use the Tahoe web or commandline api to make a
new directory in your Tahoe grid and then take note of the CAP. This
becomes a very important value which you will want to take precautions
to not lose. If you manage to lose/forget the base CAP, you will
effectively lose access to everything stored under it. Tattoo it on
your forehead if necessary.

TAHOE_PUBLIC_BASE_URL

If your django app is going to be public facing, you will need at
least one Tahoe node that is configured to accept connections from
outside hosts. Either configure a node this way or run one behind an
apache/lighttpd/nginx proxy (this can be a good setup since you can
restrict it to read-only GET requests and avoid making your grid
publically writeable). This value will then be the base of download
URLs generated. If the django app is for internal use only and
everyone has a Tahoe node running on their machine, you can set this
to "http://localhost:3456/" and file downloads will come directly via
Tahoe (this is the most efficient way to do it as it will take full
advantage of the bittorrent style swarming that Tahoe does). But
obviously, that won't work for a public site. 
