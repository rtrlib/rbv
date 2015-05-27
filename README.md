# REST BGP Validator (RBV)

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
 - cli-validator from [rtrlib]

Build `cli-validator` as described in [src/util/UTIL.md](src/util/UTIL.md) and copy its
compiled binary into `<path/to/RBV>/src/util`.

## deployment and configuration

In order to deploy and run the REST BGP Validator (RBV) - either as stand-alone
server or with apache integration - some configuration steps are required.

1. clone the [rbv] repository from github
2. clone the [rtrlib] repo from github, too
3. build RTRlib and its tools, see above or [src/util/UTIL.md](src/util/UTIL.md)
4. copy `cli-validator` binary into RBV, as described above
5. if necessary, modify [src/html/validate.html](src/html/validate.html),
   changing `localhost:5000` in URL in all form-tags to URL (FQDN) of your
   server.
6. review [src/settings.py](src/settings.py) and modify entries accordingly
7. install python requirements using pip, see above
8. start the bgp-validator daemon,
9. that's it, now proceed with stand-alone server or apache integration

## stand-alone server

You can run RBV as a stand-alone server using python only, without a big-iron
such as apache. RBV uses the integrated webserver of the[flask] microframework.
For testing just type `python rbv.py` and the server starts on `localhost` with
port 5000.

If you want public access modify `www_validator_server` entry in
[src/settings.py](src/settings.py). To allow access from any interface, set
host = `0.0.0.0` or specify a distinct interace IP address. You may also modify
the port, however ports below 1024 need system/root rights!

Note: for stand-alone server you can also you [python-virtualenv][virtualenv].

## apache integration

[wsgi]

## RPKI browser plugin

Firefox [addon]

## references

[flask]: http://flask.pocoo.org
[virtualenv]: http://docs.python-guide.org/en/latest/dev/virtualenvs/
[wsgi]: http://flask.pocoo.org/docs/0.10/deploying/mod_wsgi/

[rbv]: https://github.com/rtrlib/REST.git
[rtrlib]: https://github.com/rtrlib/rtrlib.git
[addon]: https://github.com/rtrlib/firefox-addon.git
