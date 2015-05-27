from util import *
from settings import bgp_validator_server, maintenance_timeout, validator_path

import json
import Queue
import socket
import sys
import traceback

from datetime import datetime
from subprocess import PIPE, Popen
from threading import Lock
from thread import start_new_thread
from time import sleep

validator_threads_lock = Lock()
validator_threads = {}

"""
validator_main
"""
def validator_main():
    print_log("CALL main")
    rbv_host = bgp_validator_server['host']
    rbv_port = int(bgp_validator_server['port'])

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print_info("Socket created")
    #Bind socket to local host and port
    try:
        s.bind((rbv_host, rbv_port))
    except socket.error as msg:
        print_error("Bind failed. Error Code : " + str(msg[0]) +
                    " Message " + msg[1])
        sys.exit()
    print_info("Socket bind complete")
    #Start listening on socket
    s.listen(10)
    print_info("Socket now listening")
    start_new_thread(maintenance_thread, ())
    while True:
        #wait to accept a connection - blocking call
        conn, addr = s.accept()
        print_info("Connected with " + addr[0] + ":" + str(addr[1]))
        start_new_thread(client_thread, (conn,))

    s.close()

"""
maintenance_thread

    - periodically checks all running validation threads
"""
def maintenance_thread():
    print_log("CALL maintenance_thread")
    while True:
        try:
            validator_threads_lock.acquire()
            for cs in validator_threads.keys():
                dt_now = datetime.now()
                dt_start =  validator_threads[cs]['start']
                dt_access =  validator_threads[cs]['access']
                runtime_str = str( int((dt_now - dt_start).total_seconds()) )
                errors_str = str( len(validator_threads[cs]['errors']) )
                count_str = str( validator_threads[cs]['count'] )
                dt_start_str = dt_start.strftime("%Y-%m-%d %H:%M:%S")
                dt_access_str = dt_access.strftime("%Y-%m-%d %H:%M:%S")
                mnt_str = ( "thread: " + cs +
                            ", started: " + dt_start_str +
                            ", last access: " + dt_access_str +
                            ", runtime: " + runtime_str + "s" +
                            ", counter: " + count_str +
                            ", errors: " + errors_str
                            )
                print_log(mnt_str)
        except Exception, e:
            print_error("Error during maintenance! Failed with %s" % e.message)
        finally:
            validator_threads_lock.release()
        sleep(maintenance_timeout)

"""
client_thread

    - handels incoming client connections and queries
    - starts validation_thread if necessary
"""
def client_thread(conn):
    print_log("CALL client_thread")
    data = conn.recv(1024)
    try:
        query = json.loads(data)
    except ValueError:
        print_error("Error decoding query into JSON!")
        conn.sendall("Invalid query data, must be JSON!\n")
        conn.close()
    else:
        query['conn'] = conn
        cache_server = query['cache_server']
        if not cache_server_valid(cache_server):
            print_error("Invalid cache server (%s)!" % cache_server)
            conn.close()
            return
        # Start a thread for the current cache server if necessary
        validator_threads_lock.acquire()
        try:
            global validator_threads
            if cache_server not in validator_threads:
                validator_threads[cache_server] = dict()
                new_queue = Queue.Queue()
                validator_threads[cache_server]['queue'] = new_queue
                validator_threads[cache_server]['thread'] = \
                    start_new_thread(validator_thread,
                                     (validator_threads[cache_server]['queue'],
                                      cache_server))
                validator_threads[cache_server]['start'] = datetime.now()
                validator_threads[cache_server]['access'] = datetime.now()
                validator_threads[cache_server]['errors'] = list()
                validator_threads[cache_server]['count'] = 1
            else:
                validator_threads[cache_server]['access'] = datetime.now()
                tmp = validator_threads[cache_server]['count']
                validator_threads[cache_server]['count'] = tmp+1
        finally:
            validator_threads_lock.release()
        validator_threads[cache_server]['queue'].put(query)

"""
validator_thread

    - handels cache server connections and queries by clients
"""
def validator_thread(queue, cache_server):
    cache_host = cache_server.split(":")[0]
    cache_port = cache_server.split(":")[1]
    cache_cmd = [validator_path, cache_host, cache_port]
    validator_process = Popen(cache_cmd, stdin=PIPE, stdout=PIPE)
    print_log("CALL validator thread (%s)" % cache_server)
    while True:
        validation_entry = queue.get(True)
        conn    = validation_entry['conn']
        network = validation_entry["network"]
        masklen = validation_entry["masklen"]
        asn     = validation_entry["asn"]
        bgp_entry_str = str(network) + " " + str(masklen) + " " + str(asn)
        validator_process.stdin.write(bgp_entry_str + '\n')
        validation_result = validator_process.stdout.readline().strip()
        validity_nr =  get_validity_nr(validation_result)
        print_info(cache_server + " -> " + network + "/" + masklen +
                    "(AS" + asn + ") -> " + str(validity_nr))

        resp = dict()
        resp['cache_server'] = cache_server
        resp['network'] = network
        resp['masklen'] = masklen
        resp['asn'] = asn
        resp['validity'] = validity_nr
        try:
            conn.sendall(json.dumps(resp)+'\n')
            conn.close()
        except Exception, e:
            print_error("Error sending validation response, failed with: %s" %
                        e.message)
        if (validity_nr <= -100):
            validator_threads_lock.acquire()
            global validator_threads
            validator_threads[cache_server]['errors'].append(validity_nr)
            validator_threads_lock.release()

if __name__ == "__main__":
    try:
        validator_main()
    except KeyboardInterrupt:
        print_error("Shutdown requested by the user. Exiting...")
    except Exception:
        print_error(traceback.format_exc())
        print_error("An error occurred. Exiting...")
    finally:
        sys.exit()
