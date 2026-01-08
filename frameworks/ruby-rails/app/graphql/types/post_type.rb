module Types
  class PostType < Types::BaseObject
    field :id, ID, null: false
    field :title, String, null: false
    field :content, String, null: true
    field :created_at, GraphQL::Types::ISO8601DateTime, null: false

    field :author, Types::UserType, null: false
    field :comments, [Types::CommentType], null: false

    def author
      User.find_by(pk_user: object.fk_author)
    end

    def comments
      Comment.where(fk_post: object.pk_post)
    end
  end
end
