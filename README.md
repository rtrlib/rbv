# REST BGP Validator (RBV)

The REST BGP Validator (RBV) allows to validate the origin AS (*autonomous
system*) of an IP prefix announced by the BGP (*Border Gateway Protocol*)
control plane of the Internet. For the validation process RBV uses the
[RTRlib][rtrlib] to access and query RPKI cache servers.

It offers a RESTful interface to web-applications for validation queries, and
simple website offering the same service in a user-friendly manner. Further, it
is the backend for the RPKI browser plugin available for [Firefox][firefox]
and [Chrome][chrome].

## requirements

Python modules:
 - [flask]
 - werkzeug

these can be installed using `pip`:
```
$ cd <path/to/RBV>/src
$ pip install -r requirements.txt
```
external tools:
 - URL of a working RPKI cache server
 - cli-validator from [rtrlib]

Build `cli-validator` as described in [src/util/UTIL.md](src/util/UTIL.md) and
copy its compiled binary into `<path/to/RBV>/src/util`.

Optional packages, for apache integration:
 - Apache webserver
 - mod_wsgi for apache

These packages are available for all major OS releases and platforms, or
compile and install from source.

## deployment and configuration

In order to deploy and run the REST BGP Validator (RBV) - either as stand-alone
server or with apache integration - some configuration steps are required.

1. clone the [rbv] repository from github
2. clone the [rtrlib] repo from github, too
3. build RTRlib and its tools, see above or [src/util/UTIL.md](src/util/UTIL.md)
4. copy `cli-validator` binary into RBV, as described above
5. if necessary, modify [src/html/validate.html](src/html/validate.html),
   changing `localhost:5000` in *action* attribute of all HTML form-tags to the
   URL (FQDN) of your server.
6. review [src/settings.py](src/settings.py) and modify entries accordingly
7. install python requirements using pip, see above
8. start the bgp-validator daemon: `python validator.py`
9. that's it, now proceed with stand-alone server or apache integration

## stand-alone server

You can run RBV as a stand-alone server using python only, without a big-iron
such as apache. RBV uses the integrated webserver of the [flask] microframework.
For testing just type `python rbv.py` and the server starts on *localhost* with
port *5000*. Point your browser to http://localhost:5000.

If you want public access modify `www_validator_server` entry in
[src/settings.py](src/settings.py). To allow access from any interface, set
host = `0.0.0.0` or specify a distinct interface IP address. You may also modify
the port, however ports below 1024 need system/root rights!

Note: for stand-alone server you can also use [python-virtualenv][virtualenv].

## apache integration

Using [mod_wsgi][wsgi] integrating RBV (flask app) into an apache webserver is
simple.
First, install apache and mod_wsgi, and follow the deployment and configuration
steps, as described above.
Second, modify *rbv_base_path* in [src/settings.py](src/settings.py) matching
the `src` directory of RBV clone.
Third, modify [etc/rbv_wsgi.conf](etc/rbv_wsgi.conf) according to your server
environment.
The *user* in the `rbv_wsgi.conf` must also have read-write access to the RBV
path and its subdirectories - **do not** use *root* here, but any other
non-priveledge user (even your own account) is fine.
Copy `rbv_wsgi.conf` to `/etc/apache2/sites-available` and create a sym-link in
`sites-enabled`.

**Note1:** apache v2.2 and v2.4 use different access rules, see comments in file
`rbv_wsgi.conf`.

**Note2:** depending on your apache configuration (multiple websites), further
steps might be necessary.

## RPKI browser plugin

[Firefox-Addon][firefox]

## references

[flask]: http://flask.pocoo.org
[virtualenv]: http://docs.python-guide.org/en/latest/dev/virtualenvs/
[wsgi]: http://flask.pocoo.org/docs/0.10/deploying/mod_wsgi/

[rbv]: https://github.com/rtrlib/REST.git
[rtrlib]: https://github.com/rtrlib/rtrlib.git
[firefox]: https://github.com/rtrlib/firefox-addon.git
[chrome]: https://github.com/rtrlib/chrome-extension.git
