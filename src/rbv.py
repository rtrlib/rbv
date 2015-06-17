from flask import Flask, Response
from flask.globals import request
from flask_restful import reqparse, abort, Api, Resource
from threading import Lock
from werkzeug.utils import redirect
from werkzeug.useragents import UserAgent
import json
import os.path

from util import *
from settings import *
import handler

app = Flask(__name__, static_folder="html")
api = Api(app)

parser = reqparse.RequestParser()
default_cache_server_str = (default_cache_server['host'] + ":" +
                            default_cache_server['port'])
parser.add_argument('cache_server', type=str, default=default_cache_server_str)
default_ip2as_mapping_str = default_ip2as_mapping['name']
parser.add_argument('ip2as', type=str, default=default_ip2as_mapping_str)

file_lock = Lock()
vlog_lines = 0

## private functions ##

"""
_check_request

    - internal function to check request params
"""
def _check_request(request, version):
    print_info("CALL _check_request")
    if request.method == 'POST':
        if "cache_server" not in request.form:
            return "No cache server defined."
        if (version == 1) and ("prefix" not in request.form):
            return "No IP prefix defined."
        if (version == 1) and ("asn" not in request.form):
            return "No AS number defined."
        if (version == 2) and ("host" not in request.form):
            return "No IP address defined"
        if (version == 2) and ("ip2as" not in request.form):
            return "No IP2AS mapping defined"
    elif request.method == 'GET':
        if "cache_server" not in request.args:
            return "No cache server defined."
        if (version == 1) and ("prefix" not in request.args):
            return "No IP prefix defined."
        if (version == 1) and ("asn" not in request.args):
            return "No AS number defined."
        if (version == 2) and ("host" not in request.args):
            return "No IP address defined"
        if (version == 2) and ("ip2as" not in request.args):
            return "No IP2AS mapping defined"
    else:
        return "Invalid request"
    return None

def _metadata(request):
    print_info("CALL _metadata")
    url = request.url
    remote_addr = "0.0.0.0"
    if request.headers.getlist("X-Forwarded-For"):
        remote_addr = request.headers.getlist("X-Forwarded-For")[0]
    else:
        remote_addr = request.remote_addr
    ua_str = str(request.user_agent)
    ua = UserAgent(ua_str)
    platform = ua.platform
    browser = ua.browser
    print_info( "Client IP: " + remote_addr +
                ", OS: " + platform +
                ", browser: " + browser)
    return url, remote_addr, platform, browser

"""
_log

    - internal function for logging
"""
def _log(info):
    if validation_log['enabled']:
        try:
            file_lock.acquire()
            global vlog_lines
            # got lock, now check if logrotate is enabled
            if (validation_log['rotate'] and
                os.path.isfile(validation_log['file']) and
                (vlog_lines==0 or vlog_lines==validation_log['maxlines'])):
                        log_rotate(validation_log['file'])
                        vlog_lines = 0
            with open(validation_log['file'], "ab") as f:
                ventry = ';'.join(str(x) for x in info)
                f.write(ventry+'\n')
            vlog_lines = vlog_lines+1
        except Exception, e:
            print_error("Error writing validation log, failed with: %s" %
                        e.message)
        finally:
            file_lock.release()

def _modify_response(rdata):
    ret = dict()
    vr = dict()
    route = dict()
    route['origin_asn'] = 'AS'+rdata['asn']
    route['prefix'] = rdata['prefix']
    validity = dict()
    validity['state'] = rdata['message']
    validity['description'] = rdata['message']
    vrp = dict()
    vrp['matched'] = list()
    vrp['unmatched_as'] = list()
    vrp['unmatched_length'] = list()
    validity['VRPs'] = vrp
    vr['route'] = route
    vr['validity'] = validity
    ret['validated_route'] = vr
    return ret

## public functions ##

### restful API classes ###
class RAv1(Resource):
    def get(self, asnum, prefix, masklen):
        print_log ("CALL GETv1")
        args = parser.parse_args()
        vdata = dict()
        vdata['version'] = 1
        vdata['cache_server'] = args['cache_server']
        vdata['prefix'] = prefix+"/"+masklen
        vdata['asn'] = asnum[2:]
        response_data = handler.validate(vdata)
        # logging infos
        log_datetime = datetime.now()
        log_ts_str = log_datetime.strftime('%Y-%m-%d %H:%M:%S')
        url, remote_addr, platform, browser = _metadata(request)
        info = [log_ts_str, remote_addr, platform, browser,url,
                response_data['cache_server'], response_data['prefix'],
                response_data['asn'], response_data['validity']['status']]
        _log(info)
        #return _modify_response(response_data)
        return response_data['validity']

class RAv2(Resource):
    def get(self, host):
        print_log ("CALL GETv2")
        args = parser.parse_args()
        vdata = dict()
        vdata['version'] = 2
        vdata['cache_server'] = args['cache_server']
        vdata['host'] = host
        vdata['ip2as'] = args['ip2as']
        response_data = handler.validate(vdata)
        # logging infos
        log_datetime = datetime.now()
        log_ts_str = log_datetime.strftime('%Y-%m-%d %H:%M:%S')
        url, remote_addr, platform, browser = _metadata(request)
        info = [log_ts_str, remote_addr, platform, browser,url,
                response_data['cache_server'], response_data['prefix'],
                response_data['asn'], response_data['validity']['status']]
        _log(info)
        #return _modify_response(response_data)
        return response_data['validity']

### restful API ###
api.add_resource(RAv1, '/api/v1/validity/<asnum>/<prefix>/<masklen>')
api.add_resource(RAv2, '/api/v2/validity/<host>')

### default handle ###
@app.route('/')
def html():
    return redirect("/html/validate.html")

### deprecated api ###

# Validation Service
@app.route('/validator/api/v2', methods=['GET', 'POST'])
def online_validator_v20():
    print_log("CALL online_validator_v20")
    check = _check_request(request, 2)
    if check is not None:
        error = dict()
        error['message'] = check
        response_code = 400
        response_json = json.dumps(error)
    else:
        vdata = dict()
        vdata['version'] = 2
        if request.method == 'POST':
            vdata['cache_server'] = str(request.form['cache_server']).strip()
            vdata['host'] = str(request.form['host']).strip()
            vdata['ip2as'] = str(request.form['ip2as']).strip()
        elif request.method == 'GET':
            vdata['cache_server'] = str(request.args['cache_server']).strip()
            vdata['host'] = str(request.args['host']).strip()
            vdata['ip2as'] = str(request.args['ip2as']).strip()
        response_data = handler.validate(vdata)

        print_info (response_data)

        response_data_min = dict()
        response_data_min['cache_server'] = response_data['cache_server']
        response_data_min['asn'] = response_data['asn']
        response_data_min['prefix'] = response_data['prefix']
        response_data_min['message'] = response_data['validity']['status']
        response_data_min['code'] = response_data['validity']['code']
        # remap validation code to support old/deprecated plugins
        if response_data['validity']['code'] == 0:      # valid
            response_data_min['code'] = 1
        elif response_data['validity']['code'] == 1:    # notfound
            response_data_min['code'] = -1
        elif response_data['validity']['code'] <=4:     # invalid
            response_data_min['code'] = 0

        response_json = json.dumps( response_data_min, sort_keys=True,
                                    indent=2, separators=(',', ': '))
        response_code = 200
        print_info(response_json)
        # logging infos
        log_datetime = datetime.now()
        log_ts_str = log_datetime.strftime('%Y-%m-%d %H:%M:%S')
        url, remote_addr, platform, browser = _metadata(request)
        info = [log_ts_str, remote_addr, platform, browser,url,
                response_data['cache_server'], response_data['prefix'],
                response_data['asn'], response_data['validity']['status']]
        _log(info)
    return response_json, response_code

# Validation Service
@app.route('/validator/v1.1', methods=['GET', 'POST'])
@app.route('/validator/api/v1', methods=['GET', 'POST'])
def online_validator_v11():
    print_log("CALL online_validator_v11")
    check = _check_request(request, 1)
    if check is not None:
        error = dict()
        error['message'] = check
        response_code = 400
        response_json = json.dumps(error)
    else:
        vdata = dict()
        vdata['version'] = 1
        if request.method == 'POST':
            vdata['cache_server'] = str(request.form['cache_server']).strip()
            vdata['prefix'] = str(request.form['prefix']).strip()
            vdata['asn'] = str(request.form['asn']).strip()
        elif request.method == 'GET':
            vdata['cache_server'] = str(request.args['cache_server']).strip()
            vdata['prefix'] = str(request.args['prefix']).strip()
            vdata['asn'] = str(request.args['asn']).strip()
        response_data = handler.validate(vdata)

        response_data_min = dict()
        response_data_min['cache_server'] = response_data['cache_server']
        response_data_min['asn'] = response_data['asn']
        response_data_min['prefix'] = response_data['prefix']
        response_data_min['message'] = response_data['validity']['status']
        response_data_min['code'] = response_data['validity']['code']
        # remap validation code to support old/deprecated plugins
        if response_data['validity']['code'] == 0:      # valid
            response_data_min['code'] = 1
        elif response_data['validity']['code'] == 1:    # notfound
            response_data_min['code'] = -1
        elif response_data['validity']['code'] <=4:     # invalid
            response_data_min['code'] = 0

        response_json = json.dumps( response_data_min, sort_keys=True,
                                    indent=2, separators=(',', ': '))
        print_info(response_json)
        response_code = 200
        # logging infos
        log_datetime = datetime.now()
        log_ts_str = log_datetime.strftime('%Y-%m-%d %H:%M:%S')
        url, remote_addr, platform, browser = _metadata(request)
        info = [log_ts_str, remote_addr, platform, browser,url,
                response_data['cache_server'], response_data['prefix'],
                response_data['asn'], response_data['validity']['status']]
        _log(info)
    return response_json, response_code

if __name__ == '__main__':
    app.run(host=www_validator_server['host'],
            port=int(www_validator_server['port']),
            debug=True)
