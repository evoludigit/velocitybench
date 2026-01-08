class HealthController < ApplicationController
  def index
    render json: {
      status: 'UP',
      service: 'rails-benchmark'
    }
  end
end
