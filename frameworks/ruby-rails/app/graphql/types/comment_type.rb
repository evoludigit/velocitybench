module Types
  class CommentType < Types::BaseObject
    field :id, ID, null: false
    field :content, String, null: false
    field :created_at, GraphQL::Types::ISO8601DateTime, null: false

    field :author, Types::UserType, null: false
    field :post, Types::PostType, null: false

    def author
      User.find_by(pk_user: object.fk_author)
    end

    def post
      Post.find_by(pk_post: object.fk_post)
    end
  end
end
