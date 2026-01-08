class UsersController < ApplicationController
  def show
    user = User.find_by(id: params[:id])

    if user.nil?
      render json: { error: 'User not found' }, status: :not_found
      return
    end

    render json: {
      id: user.id,
      username: user.username,
      fullName: user.full_name,
      bio: user.bio
    }
  end

  def index
    page = params.fetch(:page, 0).to_i
    size = params.fetch(:size, 10).to_i

    users = User.order(:username).offset(page * size).limit(size)

    result = users.map do |user|
      {
        id: user.id,
        username: user.username,
        fullName: user.full_name,
        bio: user.bio
      }
    end

    render json: result
  end
end
