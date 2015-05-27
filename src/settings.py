# server environment
rbv_base_path = "."
validator_path = rbv_base_path + "/util/cli-validator"

# settings
default_cache_server = {"host":"rpki-validator.realmv6.org", "port":"8282"}
bgp_validator_server = {"host":"localhost", "port":"6414"}
www_validator_server = {"host":"localhost", "port":"5000"}

maintenance_timeout = 60
access_log = {"enabled":True, "file":"access.log"}
