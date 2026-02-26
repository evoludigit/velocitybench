# frozen_string_literal: true

Gem::Specification.new do |spec|
  spec.name          = 'velocitybench-healthcheck'
  spec.version       = '1.0.0'
  spec.authors       = ['VelocityBench Team']
  spec.email         = ['team@velocitybench.com']

  spec.summary       = 'Standardized health check library for VelocityBench Ruby frameworks'
  spec.description   = 'Provides Kubernetes-compatible health check probes (liveness, readiness, startup) for Ruby frameworks'
  spec.homepage      = 'https://github.com/velocitybench/velocitybench'
  spec.license       = 'MIT'

  spec.required_ruby_version = '>= 3.0.0'

  spec.files         = Dir['lib/**/*.rb']
  spec.require_paths = ['lib']

  spec.add_development_dependency 'rspec', '~> 3.12'
  spec.add_development_dependency 'rubocop', '~> 1.50'
end
