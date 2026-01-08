class Comment < ApplicationRecord
  self.table_name = 'benchmark.tb_comment'
  self.primary_key = 'pk_comment'

  belongs_to :author, class_name: 'User', foreign_key: 'fk_author'
  belongs_to :post, class_name: 'Post', foreign_key: 'fk_post'
end
