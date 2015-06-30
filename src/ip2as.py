from util import *
import subprocess

def get_reversed_ip (ip_str):
    ip_split = ip_str.split('.')
    if len(ip_split) != 4:
        raise ValueError
    reversed_ip_str = '.'.join( ip_split[3-i] for i in range(4) )
    return reversed_ip_str

def cymru_mapping (ip_str):
    reversed_ip_str = get_reversed_ip(ip_str)
    dig_origin = ["dig","+short",reversed_ip_str+".origin.asn.cymru.com","TXT"]
    print_info("run subprocess: " + ' '.join(dig_origin))
    p = subprocess.Popen(dig_origin,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out, err = p.communicate()
    out = out.replace('"','').strip()
    print_info ("out subprocess: " +  out)
    out_split = out.split('|')
    mapping = dict()
    mapping['ip'] = ip_str
    mapping['prefix'] = out_split[1].strip()
    mapping['asn'] = out_split[0].strip()
    print_log ("IP2AS: " + ';'.join(mapping[x] for x in mapping))
    return mapping

def cymru_asinfo (asn):
    dig_asinfo = ["dig","+short","AS"+asn+".asn.cymru.com","TXT"]
    print_info("run subprocess: " + ' '.join(dig_asinfo))
    p = subprocess.Popen(dig_asinfo,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out, err = p.communicate()
    out = out.replace('"','').strip()
    print_info ("out subprocess: " +  out)
    out_split = out.split('|')
    asinfo = dict()
    asinfo['asname'] = out_split[4].strip()
    asinfo['country'] = out_split[1].strip()
    print_log ("ASinfo: " + ';'.join(asinfo[x] for x in asinfo))
    return asinfo
