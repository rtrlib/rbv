from util import *
from settings import bgp_validator_server, validator_path, \
                     maintenance_timeout, maintenance_log, thread_max_errors

import json
import Queue
import socket
import sys
import traceback

from datetime import datetime, timedelta
from subprocess import PIPE, Popen
from threading import Lock, Thread
#from thread import start_new_thread
from time import sleep

validator_threads_lock = Lock()
validator_threads = dict()
maintenance_thread = None
maintenance_thread_queue = Queue.Queue()
mlog_lines = 0

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
    #start_new_thread(maintenance_thread,())
    global maintenance_thread
    maintenance_thread = Thread(target=maintenance_thread,
                                args=(maintenance_thread_queue,))
    maintenance_thread.start()

    while True:
        #wait to accept a connection - blocking call
        conn, addr = s.accept()
        print_info("Connected with " + addr[0] + ":" + str(addr[1]))
        ct = Thread(target=client_thread, args=(conn,))
        ct.start()
        #start_new_thread(client_thread, (conn,))

    s.close()

"""
maintenance_thread

    - periodically checks all running validation threads
"""
def maintenance_thread(mtq):
    print_log("CALL maintenance_thread")
    timeout = datetime.now() + timedelta(0,maintenance_timeout)
    while True:
        now = datetime.now()
        if not mtq.empty():
            break
        if now < timeout:
            sleep(1)
            continue
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
                dt_now_str = dt_now.strftime("%Y-%m-%d %H:%M:%S")
                dt_access_str = dt_access.strftime("%Y-%m-%d %H:%M:%S")
                # timestamp;start time;last access;cache-server;counter;errors
                mnt_str = ';'.join([dt_now_str,dt_start_str,dt_access_str,cs,count_str,errors_str])
                print_log(mnt_str)
                global mlog_lines
                if maintenance_log['enabled']:
                    if (maintenance_log['rotate'] and
                        os.path.isfile(maintenance_log['file']) and
                        (mlog_lines==0 or mlog_lines==maintenance_log['maxlines'])):
                                log_rotate(maintenance_log['file'])
                                mlog_lines = 0
                    with open(maintenance_log['file'],"ab") as f:
                        f.write(mnt_str+'\n')
                    mlog_lines = mlog_lines+1
                if ((thread_max_errors > 0) and
                   (validator_threads[cs]['errors'] > thread_max_errors)):
                    print_log("RESTART thread (%s) due to errors!" % cs)
                    restart_validator_thread(cs)

        except Exception, e:
            print_error("Error during maintenance! Failed with %s" % e.message)
        finally:
            validator_threads_lock.release()
        timeout = datetime.now() + timedelta(0,maintenance_timeout)
        print_info("maintenance_thread sleeps until: " + timeout.strftime("%Y-%m-%d %H:%M:%S") )

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
                vt = Thread(target=validator_thread,
                            args=(validator_threads[cache_server]['queue'],
                                  cache_server))
                vt.start()
                #validator_threads[cache_server]['thread'] = \
                #    start_new_thread(validator_thread,
                #                     (validator_threads[cache_server]['queue'],
                #                      cache_server))
                validator_threads[cache_server]['thread'] = vt
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
    return True

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
    run = True
    while run:
        validation_entry = queue.get(True)
        if validation_entry == "STOP":
            run = False
            break
        conn    = validation_entry['conn']
        network = validation_entry["network"]
        masklen = validation_entry["masklen"]
        asn     = validation_entry["asn"]
        bgp_entry_str = str(network) + " " + str(masklen) + " " + str(asn)

        try:
            validator_process.stdin.write(bgp_entry_str + '\n')
        except Exception, e:
            print_error("Error writing to validator process, failed with %s!" %
                        e.message)
            restart_validator_thread(cache_server)
            run = False

        try:
            validation_result = validator_process.stdout.readline().strip()
        except Exception, e:
            print_error("Error reading from validator process, failed with %s!" %
                        e.message)
            restart_validator_thread(cache_server)
            validation_result = ""
            run = False

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
        # end while
    validator_process.kill()
    return True

"""
restart_validator_thread

    - helper function to restart a validator thread after an error
"""
def restart_validator_thread(cache_server):
    print_log("restarting validator thread (%s)" % cache_server)
    validator_threads_lock.acquire()
    try:
        global validator_threads
        #validator_threads[cache_server]['thread'] = \
        #            start_new_thread(validator_thread,
        #                             (validator_threads[cache_server]['queue'],
        #                              cache_server))
        validator_threads[cache_server]['queue'].put("STOP")
        new_queue = Queue.Queue()
        validator_threads[cache_server]['queue'] = new_queue
        vt = Thread(target=validator_thread,
                    args=(validator_threads[cache_server]['queue'],
                          cache_server))
        vt.start()
        validator_threads[cache_server]['thread'] = vt

    except Exception, e:
        print_error("Error restarting validator thread (%s), failed with %s" %
                    (cache_server,e.message))
    finally:
        validator_threads_lock.release()

"""
stop_validator_thread

    - helper function to stop a validator thread after an error
"""
def stop_validator_thread(cache_server):
    print_log("stopping validator thread (%s)" % cache_server)
    validator_threads_lock.acquire()
    try:
        global validator_threads
        validator_threads[cache_server]['queue'].put("STOP")
        if validator_threads[cache_server]['thread'].is_alive():
            validator_threads[cache_server]['thread'].join()
        del validator_threads[cache_server]
    except Exception, e:
        print_error("Error stopping validator thread (%s), failed with %s" %
                    (cache_server,e.message))
    finally:
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
        for v in validator_threads:
            if validator_threads[v]['thread'].is_alive():
                print ("Waiting for validator thread to terminate ...")
                validator_threads[v]['queue'].put("STOP")
                validator_threads[v]['thread'].join()
        maintenance_thread_queue.put("STOP")
        if (maintenance_thread != None) and (maintenance_thread.is_alive()):
            print ("Waiting for maintenance thread to terminate ...")
            maintenance_thread.join()
        sys.exit()
