# frozen_string_literal: true

module VelocityBench
  module Loaders
    # GraphQL::Batch loader for users by pk_user
    class UserLoader < GraphQL::Batch::Loader
      def perform(pk_users)
        users = DB.connection[:tb_user]
          .where(pk_user: pk_users)
          .all
          .each_with_object({}) do |row, hash|
            hash[row[:pk_user]] = Models::User.new(row)
          end

        pk_users.each { |pk| fulfill(pk, users[pk]) }
      end
    end

    # GraphQL::Batch loader for posts by pk_post
    class PostLoader < GraphQL::Batch::Loader
      def perform(pk_posts)
        posts = DB.connection[:tb_post]
          .where(pk_post: pk_posts)
          .all
          .each_with_object({}) do |row, hash|
            hash[row[:pk_post]] = Models::Post.new(row)
          end

        pk_posts.each { |pk| fulfill(pk, posts[pk]) }
      end
    end

    # GraphQL::Batch loader for posts by author (fk_author)
    class PostsByAuthorLoader < GraphQL::Batch::Loader
      def initialize(limit: 50)
        @limit = limit
      end

      def perform(fk_authors)
        posts_by_author = DB.connection[:tb_post]
          .where(fk_author: fk_authors)
          .order(Sequel.desc(:created_at))
          .all
          .group_by { |row| row[:fk_author] }
          .transform_values do |rows|
            rows.take(@limit).map { |row| Models::Post.new(row) }
          end

        fk_authors.each { |fk| fulfill(fk, posts_by_author[fk] || []) }
      end
    end

    # GraphQL::Batch loader for comments by post (fk_post)
    class CommentsByPostLoader < GraphQL::Batch::Loader
      def initialize(limit: 50)
        @limit = limit
      end

      def perform(fk_posts)
        comments_by_post = DB.connection[:tb_comment]
          .where(fk_post: fk_posts)
          .order(Sequel.desc(:created_at))
          .all
          .group_by { |row| row[:fk_post] }
          .transform_values do |rows|
            rows.take(@limit).map { |row| Models::Comment.new(row) }
          end

        fk_posts.each { |fk| fulfill(fk, comments_by_post[fk] || []) }
      end
    end
  end
end
