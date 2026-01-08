module Types
  class UserType < Types::BaseObject
    field :id, ID, null: false
    field :username, String, null: false
    field :full_name, String, null: true
    field :bio, String, null: true

    field :posts, [Types::PostType], null: false
    field :comments, [Types::CommentType], null: false

    def posts
      Post.where(fk_author: object.pk_user)
    end

    def comments
      Comment.where(fk_author: object.pk_user)
    end
  end
end
