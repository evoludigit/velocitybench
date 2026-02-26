# frozen_string_literal: true

module VelocityBench
  module GraphQL
    module Types
      class BaseObject < ::GraphQL::Schema::Object
      end

      class UserType < BaseObject
        graphql_name "User"

        field :id, ID, null: false
        field :username, String, null: false
        field :full_name, String, null: true
        field :bio, String, null: true
        field :created_at, String, null: false
        field :posts, [PostType], null: false do
          argument :limit, Integer, required: false, default_value: 50
        end
        field :followers, [UserType], null: false do
          argument :limit, Integer, required: false, default_value: 50
        end
        field :following, [UserType], null: false do
          argument :limit, Integer, required: false, default_value: 50
        end

        def id
          object.id.to_s
        end

        def created_at
          object.created_at.iso8601
        end

        def posts(limit:)
          Loaders::PostsByAuthorLoader.for(limit: [limit, 50].min).load(object.pk_user)
        end

        def followers(limit:)
          # Followers relationship not implemented in benchmark schema
          []
        end

        def following(limit:)
          # Following relationship not implemented in benchmark schema
          []
        end
      end

      class PostType < BaseObject
        graphql_name "Post"

        field :id, ID, null: false
        field :title, String, null: false
        field :content, String, null: true
        field :created_at, String, null: false
        field :author, UserType, null: false
        field :comments, [CommentType], null: false do
          argument :limit, Integer, required: false, default_value: 50
        end

        def id
          object.id.to_s
        end

        def created_at
          object.created_at.iso8601
        end

        def author
          Loaders::UserLoader.for.load(object.fk_author)
        end

        def comments(limit:)
          Loaders::CommentsByPostLoader.for(limit: [limit, 50].min).load(object.pk_post)
        end
      end

      class CommentType < BaseObject
        graphql_name "Comment"

        field :id, ID, null: false
        field :content, String, null: false
        field :created_at, String, null: false
        field :author, UserType, null: true
        field :post, PostType, null: true

        def id
          object.id.to_s
        end

        def created_at
          object.created_at.iso8601
        end

        def author
          Loaders::UserLoader.for.load(object.fk_author)
        end

        def post
          Loaders::PostLoader.for.load(object.fk_post)
        end
      end

      class QueryType < BaseObject
        graphql_name "Query"

        field :ping, String, null: false

        field :user, UserType, null: true do
          argument :id, ID, required: true
        end

        field :users, [UserType], null: false do
          argument :limit, Integer, required: false, default_value: 10
        end

        field :post, PostType, null: true do
          argument :id, ID, required: true
        end

        field :posts, [PostType], null: false do
          argument :limit, Integer, required: false, default_value: 10
        end

        def ping
          "pong"
        end

        def user(id:)
          Models::User.find_by_id(id)
        end

        def users(limit:)
          Models::User.all(limit: [limit, 100].min)
        end

        def post(id:)
          Models::Post.find_by_id(id)
        end

        def posts(limit:)
          Models::Post.all(limit: [limit, 100].min)
        end
      end

      class UpdateUserInput < ::GraphQL::Schema::InputObject
        graphql_name "UpdateUserInput"

        argument :full_name, String, required: false
        argument :bio, String, required: false
      end

      class UpdatePostInput < ::GraphQL::Schema::InputObject
        graphql_name "UpdatePostInput"

        argument :title, String, required: false
        argument :content, String, required: false
      end

      class MutationType < BaseObject
        graphql_name "Mutation"

        field :update_user, UserType, null: true do
          argument :id, ID, required: true
          argument :input, UpdateUserInput, required: true
        end

        field :update_post, PostType, null: true do
          argument :id, ID, required: true
          argument :input, UpdatePostInput, required: true
        end

        def update_user(id:, input:)
          updates = {}
          updates[:full_name] = input.full_name if input.full_name
          updates[:bio] = input.bio if input.bio
          updates[:updated_at] = Time.now

          return nil if updates.empty?

          DB.connection[:tb_user].where(id: id).update(updates)
          Models::User.find_by_id(id)
        end

        def update_post(id:, input:)
          updates = {}
          updates[:title] = input.title if input.title
          updates[:content] = input.content if input.content
          updates[:updated_at] = Time.now

          return nil if updates.empty?

          DB.connection[:tb_post].where(id: id).update(updates)
          Models::Post.find_by_id(id)
        end
      end
    end
  end
end
