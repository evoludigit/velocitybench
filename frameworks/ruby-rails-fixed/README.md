# Ruby on Rails - Fixed Files

This directory contains corrected versions of the Ruby on Rails framework files with proper database schema mappings.

## Files Fixed

### Models (3 files)
- `app/models/user.rb` - Added `pk_user` primary key, fixed `fk_author` foreign keys
- `app/models/post.rb` - Added `pk_post` primary key, fixed `fk_author` and `fk_post` foreign keys
- `app/models/comment.rb` - Added `pk_comment` primary key, fixed `fk_author` and `fk_post` foreign keys

### Controllers (2 files)
- `app/controllers/users_controller.rb` - Changed `first_name`/`last_name` → `full_name`
- `app/controllers/posts_controller.rb` - Fixed `author_id` → `fk_author` queries

### GraphQL Types (3 files)
- `app/graphql/types/user_type.rb` - Changed `first_name`/`last_name` → `full_name`
- `app/graphql/types/post_type.rb` - Removed `author_id` field, fixed resolver
- `app/graphql/types/comment_type.rb` - Removed FK fields, fixed resolvers

## Key Changes

### Primary Keys
All models now declare their correct primary keys:
```ruby
self.primary_key = 'pk_user'   # Instead of default 'id'
self.primary_key = 'pk_post'
self.primary_key = 'pk_comment'
```

### Foreign Keys
All associations now use correct database column names:
```ruby
# Before (WRONG):
foreign_key: 'author_id'
foreign_key: 'post_id'

# After (CORRECT):
foreign_key: 'fk_author'
foreign_key: 'fk_post'
```

### Column Names
Controllers and GraphQL types now use correct column names:
```ruby
# Before (WRONG):
first_name, last_name

# After (CORRECT):
full_name
```

## How to Apply

Run the apply script with sudo:
```bash
sudo bash ../../apply-ruby-fixes.sh
```

This will copy all fixed files to `frameworks/ruby-rails/` directory.

## Verification

After applying, test in Rails console:
```bash
cd ../ruby-rails
bundle exec rails console

# Test model associations:
User.first.posts          # Should work now
Post.first.author         # Should work now
Comment.first.post        # Should work now
```

## File Ownership

All files in this directory are owned by `lionel:lionel` for easy editing.

The original files in `frameworks/ruby-rails/` are owned by `root:root`, which is why we need sudo to apply the fixes.
