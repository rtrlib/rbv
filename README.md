# REST BGP Validator (RBV)

## requirements

Python modules:
 - [flask]
 - werkzeug

these can be installed using `pip`:

   $ cd <path/to/RBV>/src
   $ pip install -r requirements.txt

external tools:
 - cli-validator from [rtrlib]

Build `cli-validator` as described in [./src/util/UTIL.md] and copy its
compiled binary into `<path/to/RBV>/src/util`.

## stand alone server

## apache integration

[wsgi]

## RPKI browser plugin

Firefox [addon]

## references

[flask]: http://flask.pocoo.org
[rtrlib]: https://github.com/rtrlib/rtrlib.git
[wsgi]: http://flask.pocoo.org/docs/0.10/deploying/mod_wsgi/
[addon]: https://github.com/rtrlib/firefox-addon.git
