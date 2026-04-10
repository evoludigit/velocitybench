class CommentsController < ApplicationController
  def by_post
    limit = (params[:limit] || 10).to_i.clamp(1, 100)

    post = Post.find_by(id: params[:post_id])
    return render json: [], status: :ok if post.nil?

    comments = Comment
      .where(fk_post: post.pk_post)
      .includes(:author)
      .order(created_at: :desc)
      .limit(limit)

    render json: comments.map { |c|
      {
        id: c.id,
        content: c.content,
        createdAt: c.created_at.iso8601,
        author: {
          id: c.author.id,
          username: c.author.username,
          fullName: c.author.full_name
        }
      }
    }
  end
end
