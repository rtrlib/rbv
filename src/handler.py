from util import *
from settings import *

import json
import socket
import sys
from subprocess import PIPE, Popen
from werkzeug.useragents import UserAgent

"""
validate_v11
"""
def validate_v11(request):
    if "cache_server" not in request.form:
        return "No cache server defined."
    if "prefix" not in request.form:
        return "No IP prefix defined."
    if "asn" not in request.form:
        return "No AS number defined."

    cache_server = str(request.form['cache_server']).strip()
    prefix = str(request.form['prefix']).strip()
    prefix_array = prefix.split("/")
    if len(prefix_array) != 2:
        return "Invalid IP Prefix"
    network = str(prefix_array[0]).strip()
    masklen = str(prefix_array[1]).strip()
    asn = str(request.form['asn']).strip()
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

    rbv_host = bgp_validator_server['host']
    rbv_port = int(bgp_validator_server['port'])
    validity_nr = "-127"

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

    query = dict()
    query['cache_server'] = cache_server
    query['network'] = network
    query['masklen'] = masklen
    query['asn'] = asn
    print_info("query JSON: " + json.dumps(query))
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
    if validation_log['enabled']:
        try:
            with open(validation_log['file'], "ab") as f:
                ventry = ';'.join([remote_addr,platform,browser,
                                cache_server,network,masklen,asn,
                                str(validity_nr)])
                f.write(ventry+'\n')
        except Exception, e:
            print_error("Error writing validation log, failed with: %s" %
                        e.message)
    return json.dumps({"code":validity_nr,
                       "message":get_validation_message(validity_nr)})

"""
validate_v10
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
