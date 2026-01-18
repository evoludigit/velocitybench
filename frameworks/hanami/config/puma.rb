# frozen_string_literal: true

# Puma configuration for Hanami

workers ENV.fetch("WEB_CONCURRENCY", 2).to_i
threads_count = ENV.fetch("PUMA_THREADS", 5).to_i
threads threads_count, threads_count

port ENV.fetch("PORT", 4000)
environment ENV.fetch("RACK_ENV", "production")

preload_app!

on_worker_boot do
  # Reconnect to database in forked workers
  VelocityBench::DB.disconnect if defined?(VelocityBench::DB)
end
