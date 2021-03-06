# environment
rbv_base_path = "."
validator_path = rbv_base_path + "/util/cli-validator"

# connections
default_cache_server = {"host":"rpki-validator.realmv6.org", "port":"8282"}
default_ip2as_mapping = {"name":"cymru"}
bgp_validator_server = {"host":"localhost", "port":"6414"}
www_validator_server = {"host":"localhost", "port":"5000"}

# maintenance timer
maintenance_timeout = 300
# restart thread after N errors, disable = 0
thread_max_errors = 42

# output
logging = True
verbose = True
warning = True

# log validation request/queries, file format:
#   ClientIP;ClientOS;ClientBrowser;RequestURL;CacheServer;Prefix;ASN;Validity
validation_log = {  "enabled": True,
                    "file": rbv_base_path + "/validation.log",
                    "rotate": True,
                    "maxlines": 10000}
# log maintenance information, i.e., access and errors, maxlines = 1 week
maintenance_log = { "enabled": True,
                    "file": rbv_base_path + "/maintenance.log",
                    "rotate": True,
                    "maxlines": (7*24*3600/maintenance_timeout)}
