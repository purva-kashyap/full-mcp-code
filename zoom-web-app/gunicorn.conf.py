# Gunicorn configuration file
bind = "0.0.0.0:5002"
workers = 4
worker_class = "sync"
timeout = 120
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Development
reload = True
