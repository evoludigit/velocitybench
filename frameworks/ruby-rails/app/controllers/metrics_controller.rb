class MetricsController < ApplicationController
  def index
    # Generate Prometheus format output
    output = StringIO.new
    
    # Write metrics in Prometheus format
    $prometheus_registry.metrics.each do |metric|
      output.puts "# HELP #{metric.name} #{metric.docstring}"
      output.puts "# TYPE #{metric.name} #{metric.type}"
      
      # For each metric sample
      metric.values.each do |labels, value|
        if labels.empty?
          output.puts "#{metric.name} #{value}"
        else
          label_string = labels.map { |k, v| "#{k}=\"#{v}\"" }.join(',')
          output.puts "#{metric.name}{#{label_string}} #{value}"
        end
      end
      output.puts
    end
    
    # Add custom application metrics
    output.puts "# HELP rails_thread_count Number of active threads"
    output.puts "# TYPE rails_thread_count gauge"
    output.puts "rails_thread_count #{Thread.list.size}"
    output.puts
    
    output.puts "# HELP rails_uptime_seconds Application uptime in seconds"
    output.puts "# TYPE rails_uptime_seconds counter"
    output.puts "rails_uptime_seconds #{Time.now.to_i - Rails.application.initialized_at.to_i}"
    
    render plain: output.string, content_type: 'text/plain; version=0.0.4; charset=utf-8'
  end
end
