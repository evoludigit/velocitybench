class User < ApplicationRecord
  self.table_name = 'benchmark.tb_user'
  self.primary_key = 'pk_user'

  has_many :posts, class_name: 'Post', foreign_key: 'fk_author', dependent: :destroy
  has_many :comments, class_name: 'Comment', foreign_key: 'fk_author', dependent: :destroy
end
