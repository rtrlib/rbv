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

Build `cli-validator` as described in (src/util/UTIL.md) and copy its
compiled binary into `<path/to/RBV>/src/util`.

## deployment and configuration

In order to deploy and run the REST BGP Validator (RBV) - either as stand-alone
server or with apache integration - some configuration steps are required.

1. clone the [rbv] repository from github
2. clone the [rtrlib] repo from github, too
3. build RTRlib and its tools, see above or (src/util/UTIL.md)
4. copy `cli-validator` binary into RBV, as described above
5. if necessary, modify (src/html/validate.html), changing `localhost:5000`
   in URL in all <form>-tags to URL (FQDN) of your server.
6. review (src/settings.py) and modify entries accordingly
7. that's it!

## stand-alone server

## apache integration

[wsgi]

## RPKI browser plugin

Firefox [addon]

## references

[flask]: http://flask.pocoo.org
[wsgi]: http://flask.pocoo.org/docs/0.10/deploying/mod_wsgi/

[rbv]: https://github.com/rtrlib/REST.git
[rtrlib]: https://github.com/rtrlib/rtrlib.git
[addon]: https://github.com/rtrlib/firefox-addon.git
