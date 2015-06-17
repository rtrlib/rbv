from util import *
from settings import *
from ip2as import map_cymru

import json
import socket
import sys
from datetime import datetime
from subprocess import PIPE, Popen
from urlparse import urlparse

## private functions ##

"""
_validate

    - internal function, doing actual validation
"""
def _validate(query):
    print_info("CALL _validate")
    rbv_host = bgp_validator_server['host']
    rbv_port = int(bgp_validator_server['port'])
    validation_result = None
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
        print_info(data)
        try:
            validation_result = json.loads(data)
        except:
            print_error("Error decoding JSON!")
    finally:
        s.close()
    return validation_result

## public functions ##

"""
validate

 - handels validation queries for v1 (v1.1) and v2 REST API calls
"""
def validate(vdata):
    print_log("CALL validate")
    resolve_url = False
    cache_server = vdata['cache_server']
    # handle v1.1 and v2.0 accordingly
    if vdata['version'] == 1:
        prefix = vdata['prefix']
        asn = vdata['asn']
        # end v1.1
    elif vdata['version'] == 2:
        host = vdata['host']
        ip2as = vdata['ip2as']
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
    # query data
    query = dict()
    query['cache_server'] = cache_server
    query['network'] = network
    query['masklen'] = masklen
    query['asn'] = asn
    result = _validate(query)
    # JSON response
    if vdata['version'] == 2:
        result['ip'] = ip
        result['ip2as'] = ip2as
        result['resolved'] = resolve_url
    if resolve_url:
        result['hostname'] = host
    result['prefix'] = prefix
    result['asn'] = asn
    result['cache_server'] = cache_server
    return result
