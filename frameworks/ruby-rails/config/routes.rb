Rails.application.routes.draw do
  # API Routes
  get '/api/users/:id', to: 'users#show'
  get '/api/users', to: 'users#index'
  
  get '/api/posts/:id', to: 'posts#show'
  get '/api/posts', to: 'posts#index'
  get '/api/posts/by-author/:authorId', to: 'posts#by_author'
  
  get '/api/health', to: 'health#index'

  # GraphQL endpoint
  post '/graphql', to: 'graphql#execute'

  # Metrics endpoint
  get '/metrics', to: 'metrics#index'

  # Reveal health status on /up that returns 200 if the app boots with no exceptions, otherwise 500.
  get "up" => "rails/health#show", as: :rails_health_check
end
