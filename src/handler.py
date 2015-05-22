import json
from subprocess import PIPE, Popen
from settings import validator_path

"""
Parse the validation result string from the validator C program (which uses the RTRlib),
and return the validation number, which is:
  * -1 (Not Found) or
  * 0 (Invalid) or
  * 1 (Valid) or
  * one of the error messages. See get_validation_message(..) for details.
"""
def get_validity_nr(validation_result_string):
    # To Do: logging in case of errors!!!
    if validation_result_string == "timeout":
        return -101

    if validation_result_string == "error":
        return -103

    validation_result_array = validation_result_string.split("|")

    # The validation result has not the necessary format
    if len(validation_result_array) != 3:
        return -102

    validity_str = str(validation_result_array[2]).strip()
    try:
        validity_nr = int(validity_str)
    except ValueError:
        # To Do: logging!!!
        raise Exception("Validity string is not an integer: " + validity_str)
    return validity_nr

"""
Return a validation message based on the validation number.
"""
def get_validation_message(validity_nr):
    validity_nr = str(validity_nr)
    # Return validation result
    if validity_nr == "-1":
        validity = "Not found"
    elif validity_nr == "0":
        validity = "Invalid"
    elif validity_nr == "1":
        validity = "Valid"
    elif validity_nr == "-100":
        validity = "Invalid Cache Server"
    elif validity_nr == "-101":
        validity = "Cache Server Timeout"
    elif validity_nr == "-102":
        validity = "Invalid Validation Result"
    elif validity_nr == "-103":
        validity = "Cache Server Error"
    else:
        validity = "Unknown Error"
    return validity

def validate_v11(request):
    if "cache_server" not in request.form:
        return "No cache server defined."
    if "ip" not in request.form:
        return "No IP address defined."
    if "prefix" not in request.form:
        return "No IP prefix defined."
    if "asn" not in request.form:
        return "No AS number defined."

    cache_server = str(request.form['cache_server']).strip()
    ip = str(request.form['ip']).strip()
    prefix = str(request.form['prefix']).strip()
    prefix_array = prefix.split("/")
    if len(prefix_array) != 2:
        return "Invalid IP Prefix"
    mask = str(prefix_array[1]).strip()
    asn = str(request.form['asn']).strip()

    validity_nr = "-1"

    return json.dumps({"code":validity_nr, "message":get_validation_message(validity_nr)})

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
