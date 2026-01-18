# frozen_string_literal: true

module VelocityBench
  module Models
    class User
      attr_reader :id, :pk_user, :username, :full_name, :bio, :created_at

      def initialize(attrs)
        @id = attrs[:id]
        @pk_user = attrs[:pk_user]
        @username = attrs[:username]
        @full_name = attrs[:full_name]
        @bio = attrs[:bio]
        @created_at = attrs[:created_at]
      end

      def self.find_by_id(id)
        row = DB.connection[:tb_user].where(id: id).first
        return nil unless row

        new(row)
      end

      def self.find_by_pk(pk_user)
        row = DB.connection[:tb_user].where(pk_user: pk_user).first
        return nil unless row

        new(row)
      end

      def self.all(limit: 10)
        DB.connection[:tb_user]
          .order(Sequel.desc(:created_at))
          .limit(limit)
          .map { |row| new(row) }
      end
    end

    class Post
      attr_reader :id, :pk_post, :title, :content, :fk_author, :created_at

      def initialize(attrs)
        @id = attrs[:id]
        @pk_post = attrs[:pk_post]
        @title = attrs[:title]
        @content = attrs[:content]
        @fk_author = attrs[:fk_author]
        @created_at = attrs[:created_at]
      end

      def self.find_by_id(id)
        row = DB.connection[:tb_post].where(id: id).first
        return nil unless row

        new(row)
      end

      def self.find_by_pk(pk_post)
        row = DB.connection[:tb_post].where(pk_post: pk_post).first
        return nil unless row

        new(row)
      end

      def self.all(limit: 10)
        DB.connection[:tb_post]
          .order(Sequel.desc(:created_at))
          .limit(limit)
          .map { |row| new(row) }
      end

      def self.by_author(fk_author, limit: 50)
        DB.connection[:tb_post]
          .where(fk_author: fk_author)
          .order(Sequel.desc(:created_at))
          .limit(limit)
          .map { |row| new(row) }
      end
    end

    class Comment
      attr_reader :id, :pk_comment, :content, :fk_post, :fk_author, :created_at

      def initialize(attrs)
        @id = attrs[:id]
        @pk_comment = attrs[:pk_comment]
        @content = attrs[:content]
        @fk_post = attrs[:fk_post]
        @fk_author = attrs[:fk_author]
        @created_at = attrs[:created_at]
      end

      def self.find_by_id(id)
        row = DB.connection[:tb_comment].where(id: id).first
        return nil unless row

        new(row)
      end

      def self.by_post(fk_post, limit: 50)
        DB.connection[:tb_comment]
          .where(fk_post: fk_post)
          .order(Sequel.desc(:created_at))
          .limit(limit)
          .map { |row| new(row) }
      end
    end
  end
end
