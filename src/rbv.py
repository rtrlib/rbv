from flask import Flask, Response, session
from flask.globals import request
from flask.templating import render_template
from werkzeug.utils import redirect

import handler
from settings import www_validator_server

app = Flask(__name__, static_folder="html")

@app.route('/')
def html():
    return redirect("/html/validate.html")

# Validation Service
@app.route('/validator/api/v2', methods=['GET', 'POST'])
def online_validator_v20():
    result_string = handler.validate(request, 2)
    return Response(result_string)

# Validation Service
@app.route('/validator/v1.1', methods=['GET', 'POST'])
@app.route('/validator/api/v1', methods=['GET', 'POST'])
def online_validator_v11():
    result_string = handler.validate(request, 1)
    return Response(result_string)

@app.route('/validator', methods=['GET', 'POST'])
def online_validator_v10():
    # POSTed variables. check format...
    ip = str(request.form['ip']).strip()
    prefix = str(request.form['prefix']).strip()
    prefix_array = prefix.split("/")
    if len(prefix_array) != 2:
        return "Invalid BGP prefix"
    mask = str(prefix_array[1]).strip()
    asn = str(request.form['asn']).strip()
    result_string = handler.validate_v10(ip, mask, asn)
    return result_string

if __name__ == '__main__':
    app.run(host=www_validator_server['host'],
            port=int(www_validator_server['port']))
