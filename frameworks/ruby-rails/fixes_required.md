# Ruby on Rails Schema Field Mappings - Required Fixes

## Current Issues Found

### 1. Model Associations Use Wrong Foreign Keys
**File:** `app/models/user.rb`
```ruby
# CURRENT (wrong):
has_many :posts, foreign_key: 'author_id', dependent: :destroy
has_many :comments, foreign_key: 'author_id', dependent: :destroy

# SHOULD BE:
has_many :posts, foreign_key: 'fk_author', primary_key: 'pk_user', dependent: :destroy
has_many :comments, foreign_key: 'fk_author', primary_key: 'pk_user', dependent: :destroy
```

### 2. Post Model Foreign Keys Wrong
**File:** `app/models/post.rb`
```ruby
# CURRENT (wrong):
belongs_to :author, class_name: 'User', foreign_key: 'author_id'
has_many :comments, foreign_key: 'post_id', dependent: :destroy

# SHOULD BE:
belongs_to :author, class_name: 'User', foreign_key: 'fk_author', primary_key: 'pk_user'
has_many :comments, foreign_key: 'fk_post', primary_key: 'pk_post', dependent: :destroy
```

### 3. Comment Model Foreign Keys Wrong
**File:** `app/models/comment.rb`
```ruby
# CURRENT (wrong):
belongs_to :author, class_name: 'User', foreign_key: 'author_id'
belongs_to :post, foreign_key: 'post_id'

# SHOULD BE:
belongs_to :author, class_name: 'User', foreign_key: 'fk_author', primary_key: 'pk_user'
belongs_to :post, foreign_key: 'fk_post', primary_key: 'pk_post'
```

### 4. Controllers Use Wrong Column Names
**File:** `app/controllers/users_controller.rb`
```ruby
# CURRENT (wrong):
{
  firstName: user.first_name,
  lastName: user.last_name,
}

# SHOULD BE:
{
  fullName: user.full_name,
}
```

### 5. Posts Controller Uses Wrong Foreign Key
**File:** `app/controllers/posts_controller.rb`
```ruby
# CURRENT (wrong):
authorId: post.author_id,

# SHOULD BE:
authorId: post.fk_author,
```

### 6. GraphQL Types Use Wrong Field Names
**File:** `app/graphql/types/user_type.rb`
```ruby
# CURRENT (wrong):
field :first_name, String, null: false
field :last_name, String, null: false

# SHOULD BE:
field :full_name, String, null: true
```

### 7. GraphQL Resolvers Cause N+1 Queries
**File:** `app/graphql/types/user_type.rb`
```ruby
# CURRENT (causes N+1):
def posts
  object.posts.includes(:author)
end

# SHOULD BE (with DataLoader):
def posts
  # Use DataLoader to batch load posts
end
```

## Database Schema Reference

```sql
-- User table
CREATE TABLE benchmark.tb_user (
  pk_user INT PRIMARY KEY,
  id UUID UNIQUE,
  username VARCHAR,
  full_name VARCHAR,  -- Not first_name/last_name
  bio TEXT
);

-- Post table  
CREATE TABLE benchmark.tb_post (
  pk_post INT PRIMARY KEY,
  id UUID UNIQUE,
  fk_author INT REFERENCES tb_user(pk_user),  -- Not author_id
  title VARCHAR,
  content TEXT
);

-- Comment table
CREATE TABLE benchmark.tb_comment (
  pk_comment INT PRIMARY KEY,
  id UUID UNIQUE,
  fk_post INT REFERENCES tb_post(pk_post),    -- Not post_id
  fk_author INT REFERENCES tb_user(pk_user),  -- Not author_id
  content TEXT
);
```

## Required Changes Summary

1. **Models**: Update all foreign key references from Rails conventions to CQRS schema names
2. **Controllers**: Change column references from `first_name`/`last_name` to `full_name`
3. **GraphQL Types**: Update field names to match database schema
4. **GraphQL Resolvers**: Implement DataLoader pattern to prevent N+1 queries

## Files to Modify

- `app/models/user.rb`
- `app/models/post.rb` 
- `app/models/comment.rb`
- `app/controllers/users_controller.rb`
- `app/controllers/posts_controller.rb`
- `app/graphql/types/user_type.rb`
- `app/graphql/types/post_type.rb`
- `app/graphql/types/comment_type.rb`
