# Restart Gunicorn every 950-1050 requests
# May mitigate memory leak attacks
max_requests = 1000
max_requests_jitter = 50

# Bind on all addresses it's in Docker anyways
bind = "0.0.0.0:5000"

# May thread starve /!\
workers = 1
timeout = 120

# Log on stdout
log_file = "-"
