# Puma configuration for benchmarking
threads_count = ENV.fetch('RAILS_MAX_THREADS', 8)
threads threads_count, threads_count

# Specifies the port that Puma will listen on
port ENV.fetch('PORT', 8000)

# Allow puma to be restarted by bin/rails restart command
plugin :tmp_restart

# Run the Solid Queue supervisor inside of Puma for single-server deployments
# plugin :solid_queue if ENV.fetch('SOLID_QUEUE_IN_PUMA')

# Specify the PID file
# pidfile ENV['PIDFILE'] if ENV['PIDFILE']

# Configure worker processes (set to 1 for benchmarking to avoid complexity)
workers ENV.fetch('WEB_CONCURRENCY', 1)

# Preload the application for better performance
preload_app!

# Re-establish database connections in each worker after fork
on_worker_boot do
  ActiveRecord::Base.establish_connection if defined?(ActiveRecord)
end

# Restart workers after this many requests (helps with memory leaks)
worker_timeout 3600 if ENV.fetch('RAILS_ENV', 'development') == 'development'

# Allow puma to accept connections immediately
bind "tcp://0.0.0.0:#{ENV.fetch('PORT', 8000)}"

# Enable lowlevel error reports for debugging
lowlevel_error_handler do |e|
  [500, {}, ["An error has occurred: #{e.message}"]]
end
