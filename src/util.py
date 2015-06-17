from __future__ import print_function
import settings
import sys
import gzip

import os
from datetime import datetime

## util vars and defs ##

validity_state = ['Valid','NotFound','Invalid','InvalidAS','InvalidLength']
validity_descr = [  "At least one VRP Matches the Route Prefix",
                    "No VRP Covers the Route Prefix",
                    "At least one VRP Matches the Route Prefix, but no VRP ASN or the Route Prefix length is greater than the maximum length allowed by VRP(s) matching this route origin ASN",
                    "At least one VRP Covers the Route Prefix, but no VRP ASN matches the route origin ASN",
                    "At least one VRP Covers the Route Prefix, but the Route Prefix length is greater than the maximum length allowed by VRP(s) matching this route origin ASN"]

## util functions ##

def print_log(*objs):
    if settings.logging or settings.verbose:
        print("[LOGS] .", *objs, file=sys.stdout)

def print_info(*objs):
    if settings.verbose:
        print("[INFO] ..", *objs, file=sys.stdout)

def print_warn(*objs):
    if settings.warning or settings.verbose:
        print("[WARN] ", *objs, file=sys.stderr)

def print_error(*objs):
    print("[ERROR] ", *objs, file=sys.stderr)

"""
log_rotate

 - rotates a logfile, that is rename and gzip compression
 - note: this is not thread safe, so ensure zero file access when running this!
"""
def log_rotate(file):
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    f_in = open(file, 'rb')
    f_out = gzip.open(file+"."+now_str+".gz", 'wb')
    f_out.writelines(f_in)
    f_out.close()
    f_in.close()
    os.remove(file)

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
