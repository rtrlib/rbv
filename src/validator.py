"""
This online_validator is part of the RPKI Validator extensions. It is responsible
for determining the validity of the combination of a prefix and ASN. It was built for
serving the requests from the extensions, but it can be used independently of them as well,
for example for offering a web service for RPKI validation.

The online_validator is meant to be used as a daemon. Once started, it is waiting for data
by checking the database for new entries. When a new entry is found, it is validated and
the validation result is written back to the database. This can be then sent back to the
extension.

"""

import json
import Queue
import socket
import sys
import traceback

from datetime import datetime
from subprocess import PIPE, Popen
from threading import Lock
from thread import start_new_thread

from settings import validator_path,bgp_validator_server
from util import get_validity_nr, get_validation_message

thread_timeout = 300
lock = Lock()
validator_threads = {}
validator_thread_queues = {}
validator_thread_timeouts = {}

"""
main
"""
def main():
    rbv_host = bgp_validator_server['host']
    rbv_port = int(bgp_validator_server['port'])

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print "Socket created"
    #Bind socket to local host and port
    try:
        s.bind((rbv_host, rbv_port))
    except socket.error as msg:
        print "Bind failed. Error Code : " + str(msg[0]) + " Message " + msg[1]
        sys.exit()
    print "Socket bind complete"
    #Start listening on socket
    s.listen(10)
    print "Socket now listening"
    while True:
        #wait to accept a connection - blocking call
        conn, addr = s.accept()
        print "Connected with " + addr[0] + ":" + str(addr[1])
        start_new_thread(client_thread, (conn,))

    s.close()

"""
cache_server_valid

This function should be extended to check cache server validity more profoundly.
"""
def cache_server_valid(cache_server):
        try:
            if len(cache_server.split(":")) != 2:
                return False
            host = cache_server.split(":")[0]
            port = int(cache_server.split(":")[1])
            if len(host)<1 or port<0:
                return False
            return True
        except:
            return False

"""
client_thread
"""
def client_thread(conn):
    data = conn.recv(1024)
    try:
        query = json.loads(data)
    except ValueError:
        print "Error decoding query into JSON!"
        conn.sendall("Invalid query data, must be JSON!\n")
        conn.close()
    else:
        query['conn'] = conn
        cache_server = query['cache_server']
        if not cache_server_valid(cache_server):
            print "Invalid cache server (%s)!" % cache_server
            conn.close()
            return
        # Start a thread for the current cache server if necessary
        lock.acquire()
        try:
            global validator_threads
            global validator_thread_queues
            global validator_thread_timeouts
            if cache_server not in validator_thread_queues:
                print "Create ValidatorThread (%s)" % cache_server
                new_queue = Queue.Queue()
                validator_thread_queues[cache_server] = new_queue
                validator_threads[cache_server] = start_new_thread(validator_thread, (validator_thread_queues[cache_server],cache_server))
                validator_thread_timeouts[cache_server] = datetime.now()
                #validator_threads[cache_server] = ValidatorThread(new_queue, cache_server)
                #validator_threads[cache_server].start()
            else:
                validator_thread_timeouts[cache_server] = datetime.now()
        finally:
            lock.release()
        validator_thread_queues[cache_server].put(query)

"""
validator_thread
"""
def validator_thread(queue, cache_server):
    cache_host = cache_server.split(":")[0]
    cache_port = cache_server.split(":")[1]
    cache_cmd = [validator_path, cache_host, cache_port]
    validator_process = Popen(cache_cmd, stdin=PIPE, stdout=PIPE)
    print "Started validator thread (%s)" % cache_server
    while True:
        validation_entry = queue.get(True)
        conn    = validation_entry['conn']
        network = validation_entry["network"]
        masklen = validation_entry["masklen"]
        asn     = validation_entry["asn"]
        bgp_entry_str = str(network) + " " + str(masklen) + " " + str(asn)
        validator_process.stdin.write(bgp_entry_str + '\n')
        while True:
            validation_result = validator_process.stdout.readline().strip()
            validity_nr =  get_validity_nr(validation_result)
            if validity_nr == -102:
                continue
            elif (validity_nr == -103) or (validity_nr == -101):
                print(cache_server + " -> " + get_validation_message(validity_nr))
            else:
                print(cache_server + " -> " + network + "/" + masklen +
                        "(AS" + asn + ") -> " + str(validity_nr))
                break

        resp = dict()
        resp['cache_server'] = cache_server
        resp['network'] = network
        resp['masklen'] = masklen
        resp['asn'] = asn
        resp['validity'] = validity_nr
        try:
            conn.sendall(json.dumps(resp)+'\n')
            conn.close()
        except:
            print "Error sending validation response!"
        else:
            print "Send validation response and closed client connection."

try:
    main()
except KeyboardInterrupt:
    print("Shutdown requested by the user. Exiting...")
except Exception:
    print traceback.format_exc()
    print("An error occurred. Exiting...")
finally:
    sys.exit()
