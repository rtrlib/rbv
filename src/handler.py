from util import *
from settings import *
from ip2as import map_cymru

import json
import socket
import sys
from threading import Lock
from subprocess import PIPE, Popen
from urlparse import urlparse
from werkzeug.useragents import UserAgent

file_lock = Lock()

## private functions

"""
_log

    - internal function for logging
"""
def _log(info):
    if validation_log['enabled']:
        try:
            file_lock.acquire()
            with open(validation_log['file'], "ab") as f:
                ventry = ';'.join(str(x) for x in info)
                f.write(ventry+'\n')
        except Exception, e:
            print_error("Error writing validation log, failed with: %s" %
                        e.message)
        finally:
            file_lock.release()

"""
_check_request

    - internal function to check request params
"""
def _check_request(request, version):
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

"""
_validate

    - internal function, doing actual validation
"""
def _validate(query):
    rbv_host = bgp_validator_server['host']
    rbv_port = int(bgp_validator_server['port'])
    validity_nr = "-127"
    print_info("query JSON: " + json.dumps(query))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print_info("Socket created")
    #Bind socket to local host and port
    try:
        s.connect((rbv_host, rbv_port))
    except socket.error as msg:
        print_error("Bind failed. Error Code : " + str(msg[0]) +
                    " Message " + msg[1])
        s.close()
        return "Error connecting to bgp validator!"
    print_info("Socket bind complete")
    # send query
    try:
        s.sendall(json.dumps(query))
        data = s.recv(1024)
    except Exception, e:
        print_error("Error sending query, failed with: %s" % e.message)
    else:
        try:
            resp = json.loads(data)
        except:
            print_error("Error decoding JSON!")
        else:
            if 'validity' in resp:
                validity_nr = resp['validity']
    finally:
        s.close()
    return validity_nr

## public functions

"""
validate

 - handels validation queries for v1 (v1.1) and v2 REST API calls
"""
def validate(request, version):
    # check if request contains needed values
    check = _check_request(request, version)
    resolve_url = False
    if check is not None:
        return check
    # handle v1.1 and v2.0 accordingly
    if version == 1:
        if request.method == 'POST':
            cache_server = str(request.form['cache_server']).strip()
            prefix = str(request.form['prefix']).strip()
            asn = str(request.form['asn']).strip()
        elif request.method == 'GET':
            cache_server = str(request.args['cache_server']).strip()
            prefix = str(request.args['prefix']).strip()
            asn = str(request.args['asn']).strip()
        # end v1.1
    elif version == 2:
        if request.method == 'POST':
            cache_server = str(request.form['cache_server']).strip()
            host = str(request.form['host']).strip()
            ip2as = str(request.form['ip2as']).strip()
        elif request.method == 'GET':
            cache_server = str(request.args['cache_server']).strip()
            host = str(request.args['host']).strip()
            ip2as = str(request.args['ip2as']).strip()
        # if standard url, parse it and get hostname
        if host.find('://') != -1:
            url = urlparse(host)
            host = url.hostname
        # if url w/o scheme and path, but with port
        elif host.find(':') != -1:
            port = host.find('/')
            host = host[:port]
        # if url w/o scheme and port, but with path
        elif host.find('/') != -1:
            path = host.find('/')
            host = host[:path]
        ip = socket.gethostbyname(host)
        if ip != host:
            resolve_url = True
        try:
            res = map_cymru(ip)
            prefix = res['prefix']
            asn = res['asn']
        except Exception, e:
            print_error("Error mapping IP to AS, failed with: %s" % e.message)
            return "Mapping error"
        # end v2.0
    else:
        return "Invalid version information"
    # split prefix
    prefix_array = prefix.split("/")
    if len(prefix_array) != 2:
        return "Invalid IP Prefix"
    network = str(prefix_array[0]).strip()
    masklen = str(prefix_array[1]).strip()
    # gather meta data
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
    # query data
    query = dict()
    query['cache_server'] = cache_server
    query['network'] = network
    query['masklen'] = masklen
    query['asn'] = asn
    validity_nr = _validate(query)
    # logging infos
    info = [remote_addr,platform,browser,url,
            cache_server,prefix,asn,str(validity_nr)]
    _log(info)
    # JSON response
    validity = dict()
    if version == 2:
        validity['ip'] = ip
        validity['ip2as'] = ip2as
        validity['resolved'] = resolve_url
    if resolve_url:
        validity['hostname'] = host
    validity['prefix'] = prefix
    validity['asn'] = asn
    validity['cache_server'] = cache_server
    validity['code'] = validity_nr
    validity['message'] = get_validation_message(validity_nr)
    return json.dumps(validity, sort_keys=True, indent=2, separators=(',', ': '))

"""
validate_v10

    - for backwards compatibility, otherwise deprecated
"""
def validate_v10(ip, mask, asn):
    host = default_cache_server["host"]
    port = default_cache_server["port"]
    cmd = [validator_path, host, port]
    cproc = Popen(cmd, stdin=PIPE, stdout=PIPE)
    bgp_entry_str = ip + " " + mask + " " + asn
    cproc.stdin.write(bgp_entry_str + '\n')
    validation_result_string = cproc.stdout.readline().strip()
    cproc.kill()

    validity_nr = get_validity_nr(validation_result_string)
    return get_validation_message(validity_nr)
