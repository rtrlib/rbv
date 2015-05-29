from util import *
import subprocess

def get_reversed_ip (ip_str):
    ip_split = ip_str.split('.')
    if len(ip_split) != 4:
        raise ValueError
    reversed_ip_str = '.'.join( ip_split[3-i] for i in range(4) )
    return reversed_ip_str

def map_cymru (ip_str):
    reversed_ip_str = get_reversed_ip(ip_str)
    dig_cmd = ["dig","+short",reversed_ip_str+".origin.asn.cymru.com","TXT"]
    print_info("run subprocess: " + ' '.join(dig_cmd))
    p = subprocess.Popen(dig_cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out, err = p.communicate()
    out = out.replace('"','').strip()
    print_info ("out subprocess: " +  out)
    out_split = out.split('|')
    result = dict()
    result['ip'] = ip_str
    result['prefix'] = out_split[1].strip()
    result['asn'] = out_split[0].strip()
    result['country'] = out_split[2].strip()
    print_log ("IP2AS: " + ';'.join(result[x] for x in result))
    return result
