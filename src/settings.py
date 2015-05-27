# environment
rbv_base_path = "."
validator_path = rbv_base_path + "/util/cli-validator"

# connections
default_cache_server = {"host":"rpki-validator.realmv6.org", "port":"8282"}
bgp_validator_server = {"host":"localhost", "port":"6414"}
www_validator_server = {"host":"localhost", "port":"5000"}

# maintenance
maintenance_timeout = 300
thread_timeout = maintenance_timeout*5
thread_errors = 42

# output
logging = True
verbose = True
warning = True

# log validation request/queries, file format:
#   ClientIP;ClientOS;ClientBrowser;RequestURL;CacheServer;Prefix;ASN;Validity
validation_log = {"enabled":True, "file": rbv_base_path + "/validation.log"}
