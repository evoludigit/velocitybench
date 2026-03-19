class PostsController < ApplicationController
  def show
    post = Post.includes(:author).find_by(id: params[:id])

    if post.nil?
      render json: { error: 'Post not found' }, status: :not_found
      return
    end

    render json: {
      id: post.id,
      title: post.title,
      content: post.content,
      authorId: post.author.id,
      createdAt: post.created_at.iso8601
    }
  end

  def index
    page = params.fetch(:page, 0).to_i
    size = params.fetch(:size, 10).to_i

    posts = Post.includes(:author)

    if params.key?(:published)
      published_val = params[:published].to_s.downcase == "true" || params[:published].to_s == "1"
      posts = posts.where(published: published_val)
    end

    posts = posts.order(created_at: :desc)
                 .offset(page * size)
                 .limit(size)

    if params[:with_author] == "true"
      result = posts.map do |post|
        {
          id: post.id,
          title: post.title,
          content: post.content,
          author: { username: post.author.username, fullName: post.author.full_name },
          createdAt: post.created_at.iso8601
        }
      end
    else
      result = posts.map do |post|
        {
          id: post.id,
          title: post.title,
          content: post.content,
          authorId: post.author.id,
          createdAt: post.created_at.iso8601
        }
      end
    end

    render json: result
  end

  def by_author
    author_id = params[:authorId]
    page = params.fetch(:page, 0).to_i
    size = params.fetch(:size, 10).to_i

    # Find author by UUID id, get pk_user for query
    author = User.find_by(id: author_id)
    return render json: [], status: :ok if author.nil?

    posts = Post.where(fk_author: author.pk_user)
                .includes(:author)
                .order(created_at: :desc)
                .offset(page * size)
                .limit(size)

    result = posts.map do |post|
      {
        id: post.id,
        title: post.title,
        content: post.content,
        authorId: post.author.id,
        createdAt: post.created_at.iso8601
      }
    end

    render json: result
  end
end
