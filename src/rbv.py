from flask import Flask
from flask import Response, session
from flask.globals import request
from flask.templating import render_template
from werkzeug.utils import redirect
import handler
app = Flask(__name__, static_folder="html")

@app.route('/')
def html():
    return redirect("/html/validate.html")

# Validation Service
@app.route('/validator/v1.1', methods=['GET', 'POST'])
def online_validator_v11():
    result_string = handler.validate_v11(request)
    return Response(result_string)

@app.route('/validator', methods=['GET', 'POST'])
def online_validator_v10():
    # POSTed variables. check format...
    ip = str(request.form['ip']).strip()
    # example: 63.245.215.70
    prefix = str(request.form['prefix']).strip()
    # example:  63.245.214.0/23
    prefix_array = prefix.split("/")
    if len(prefix_array) != 2:
        return "Invalid BGP Prefix"
    mask = str(prefix_array[1]).strip()
    asn = str(request.form['asn']).strip()
    # example: 36856
    result_string = handler.validate_v10(ip, mask, asn)
    return result_string

if __name__ == '__main__':
    app.run()
