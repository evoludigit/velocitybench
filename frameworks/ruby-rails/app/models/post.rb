class Post < ApplicationRecord
  self.table_name = 'benchmark.tb_post'
  self.primary_key = 'pk_post'

  belongs_to :author, class_name: 'User', foreign_key: 'fk_author'
  has_many :comments, class_name: 'Comment', foreign_key: 'fk_post', dependent: :destroy
end
