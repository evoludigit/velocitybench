# frozen_string_literal: true

require "bundler/setup"
require "hanami"
require "hanami/router"
require "sequel"
require "graphql"
require "graphql/batch"
require "oj"

# Load application files
require_relative "../lib/db"
require_relative "../lib/models"
require_relative "../lib/loaders"
require_relative "../lib/graphql/types"
require_relative "../lib/graphql/schema"
require_relative "../app/actions/graphql_action"
require_relative "../app/actions/health_action"
require_relative "../app/actions/metrics_action"

module Hanami
  class App < Hanami::App
    config.root = File.expand_path("..", __dir__)
  end

  def self.app
    @app ||= Hanami::Router.new do
      post "/graphql", to: Actions::GraphqlAction.new
      get "/health", to: Actions::HealthAction.new
      get "/metrics", to: Actions::MetricsAction.new
    end
  end
end
