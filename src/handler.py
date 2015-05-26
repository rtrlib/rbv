import json
import socket
import sys
from subprocess import PIPE, Popen

from settings import validator_path,bgp_validator_client,default_cache_server
from util import get_validity_nr, get_validation_message

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

    if request.headers.getlist("X-Forwarded-For"):
        client_ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        client_ip = request.remote_addr
    user_agent = request.user_agent
    print "Client IP " + client_ip

    rbv_host = bgp_validator_server['host']
    rbv_port = int(bgp_validator_server['port'])
    validity_nr = "-1"

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print 'Socket created'
    #Bind socket to local host and port
    try:
        s.connect((rbv_host, rbv_port))
    except socket.error as msg:
        print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        s.close()
        return "Error connecting to bgp validator!"
    print 'Socket bind complete'
    query = dict()
    query = ['']
    query['cache_server'] = cache_server
    query['network'] = network
    query['masklen'] = masklen
    query['asn'] = asn
    try:
        s.sendall(json.dumps(query))
        data = s.recv(1024)
    except Exception, e:
        print "Error sending query."
    else:
        try:
            resp = json.loads(data)
        except:
            print "Error decoding JSON!"
        else:
            if 'validity' in resp:
                validity_nr = resp['validity']
    finally:
        s.close()
    return json.dumps({"code":validity_nr,
                       "message":get_validation_message(validity_nr)})

def validate_v10(ip, mask, asn):
    host = default_cache_server["host"]
    port = default_cache_server["port"]
    cmd = [validator_path, host, port]
    cproc = Popen(cmd, stdin=PIPE, stdout=PIPE)
    bgp_entry_str = ip + " " + mask + " " + asn
    #validation_result_string = cproc.communicate(bgp_entry_str + '\n')[0]
    cproc.stdin.write(bgp_entry_str + '\n')
    validation_result_string = cproc.stdout.readline().strip()
    cproc.kill()

    validity_nr = get_validity_nr(validation_result_string)
    return get_validation_message(validity_nr)
