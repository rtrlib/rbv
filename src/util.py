"""
get_validity_nr

Parse the validation result string from the validator C program (uses rtrlib),
and return the validation number, which is:
  * -1 (Not Found) or
  * 0 (Invalid) or
  * 1 (Valid) or
  * one of the error messages.
See get_validation_message(..) for details.
"""
def get_validity_nr(validation_result_string):
    if validation_result_string == "timeout":
        return -101

    if validation_result_string == "error":
        return -103

    if validation_result_string == "input error":
        return -104

    validation_result_array = validation_result_string.split("|")

    # The validation result has not the necessary format
    if len(validation_result_array) != 3:
        return -102

    validity_str = str(validation_result_array[2]).strip()
    try:
        validity_nr = int(validity_str)
    except ValueError:
        print "Validity string is not an integer: " + validity_str
        validity_nr = -102
    return validity_nr

"""
get_validation_message

Return a validation message based on the validation number.
"""
def get_validation_message(validity_nr):
    try:
        validity_nr = int(validity_nr)
    except:
        validity = "Unknown Error"
    else:
        # Return validation result
        if validity_nr == 1:
            validity = "Valid"
        elif validity_nr == 0:
            validity = "Invalid"
        elif validity_nr == -1:
            validity = "Not Found"
        elif validity_nr == -100:
            validity = "Cache Server Invalid"
        elif validity_nr == -101:
            validity = "Cache Server Timeout"
        elif validity_nr == -102:
            validity = "Invalid Validation Result"
        elif validity_nr == -103:
            validity = "Cache Server Error"
        elif validity_nr == -104:
            validity = "Cache Server Input Error"
        else:
            validity = "Unknown Error"
    return validity

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
