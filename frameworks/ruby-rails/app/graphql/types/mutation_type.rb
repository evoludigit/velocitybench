module Types
  class MutationType < GraphQL::Schema::Object
    field :update_user, Types::UserType, null: true do
      argument :id, ID, required: true
      argument :full_name, String, required: false
      argument :bio, String, required: false
    end

    def update_user(id:, full_name: nil, bio: nil)
      # Validate inputs
      if full_name && full_name.length > 255
        raise GraphQL::ExecutionError, "Full name must be at most 255 characters"
      end
      if bio && bio.length > 1000
        raise GraphQL::ExecutionError, "Bio must be at most 1000 characters"
      end

      user = User.find_by(id: id)
      return nil unless user

      user.full_name = full_name if full_name
      user.bio = bio if bio
      user.updated_at = Time.current

      user.save!
      user
    end
  end
end