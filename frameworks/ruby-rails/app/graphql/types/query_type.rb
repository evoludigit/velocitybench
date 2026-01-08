module Types
  class QueryType < GraphQL::Schema::Object
    field :user, Types::UserType, null: true do
      argument :id, ID, required: true
    end

    def user(id:)
      User.find_by(id: id)
    end

    field :users, [Types::UserType], null: false do
      argument :first, Int, required: false, default_value: 10
    end

    def users(first:)
      User.order(:username).limit(first)
    end

    field :post, Types::PostType, null: true do
      argument :id, ID, required: true
    end

    def post(id:)
      Post.includes(:author).find_by(id: id)
    end

    field :posts, [Types::PostType], null: false do
      argument :first, Int, required: false, default_value: 10
    end

    def posts(first:)
      Post.includes(:author).order(created_at: :desc).limit(first)
    end

    field :posts_by_user, [Types::PostType], null: false do
      argument :user_id, ID, required: true
      argument :first, Int, required: false, default_value: 10
    end

    def posts_by_user(user_id:, first:)
      # Find user by UUID, then query by pk_user
      user = User.find_by(id: user_id)
      return [] if user.nil?

      Post.where(fk_author: user.pk_user)
          .includes(:author)
          .order(created_at: :desc)
          .limit(first)
    end

    field :comments_by_post, [Types::CommentType], null: false do
      argument :post_id, ID, required: true
      argument :first, Int, required: false, default_value: 10
    end

    def comments_by_post(post_id:, first:)
      # Find post by UUID, then query by pk_post
      post = Post.find_by(id: post_id)
      return [] if post.nil?

      Comment.where(fk_post: post.pk_post)
             .includes(:author, :post)
             .order(created_at: :asc)
             .limit(first)
    end
  end
end
