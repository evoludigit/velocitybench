---
# **[Pattern] Full-Stack Framework Patterns (Rails & Django) Reference Guide**

---

## **1. Overview**
This reference guide outlines best practices for implementing **Full-Stack Framework Patterns** using **Ruby on Rails** and **Django**, two leading full-stack web frameworks. It covers architecture principles, component interactions, and scalable implementation strategies for web applications, ensuring consistency, maintainability, and performance.

Key considerations include:
- **MVC/MVT Architecture**: Rails (MVC) and Django (MVT—Model-View-Template) patterns with variations.
- **Database Integration**: ORM (ActiveRecord/ORM) and migration management.
- **Security & Validation**: Built-in mechanisms for data integrity and protection.
- **REST API Design**: Structured endpoints and authentication.
- **Performance Optimization**: Caching, asset pipelines, and database indexing.

This guide assumes familiarity with basic Rails/Django concepts and object-oriented programming.

---

## **2. Schema Reference**

| **Category**       | **Rails (MVC)**                          | **Django (MVT)**                        | **Shared Best Practice**                     |
|--------------------|----------------------------------------|----------------------------------------|---------------------------------------------|
| **Model Layer**    | ActiveRecord (PostgreSQL/MySQL/SQLite) | Django ORM (PostgreSQL/MySQL)          | Use migrations (`rails db:migrate`, `python manage.py migrate`). |
| **Serialization**  | `to_json`, `serializable_hash` (Rails API) | Django REST Framework (DRF) serializers | Prefer lightweight serialization (e.g., JSON API or DRF). |
| **View Layer**     | ERB, Haml, or Slim templates           | Django Templates (`{% %}` syntax)      | Separate logic from presentation.           |
| **Routing**        | `config/routes.rb` (RESTful conventions) | `urls.py` (Naming: `user-detail/`)     | Prefer RESTful routes with resource naming. |
| **Authentication** | Devise (3rd-party) or custom           | Django’s `auth` app + `allauth`        | Use OAuth2/JWT for APIs (e.g., `rack-cors`). |
| **Caching**        | Redis (via `redis-rails`)               | Memcached (`django-redis`)             | Implement TTL (Time-To-Live) for cache keys. |
| **Assets**         | Sprockets (CSS/JS bundling)             | Whitesource (WSGI) or `django-compressor` | Minify assets in production.               |
| **Background Jobs**| Sidekiq (Redis)                         | Celery + Redis/RabbitMQ                | Use queues for async tasks (e.g., emails).  |
| **Testing**        | RSpec + Capybara                       | Django’s `unittest` + `pytest`         | Test models, views, and API endpoints.      |
| **Deployment**     | Pascaline, Capistrano, or Docker        | Gunicorn + Nginx + Docker              | Use environment variables (`rails env` or `os.getenv`). |

---

## **3. Query Examples**

### **3.1 Database Queries**
#### **Rails (ActiveRecord)**
```ruby
# Fetch all active users with pagination
ActiveRecord::Base.connection.execute("SELECT * FROM users WHERE is_active = true LIMIT 10 OFFSET 0")

# Soft delete (scoped)
User.active.limit(10).offset(0)

# Counter cache for performance
User.include(:posts).where(posts: { published: true })
```

#### **Django (ORM)**
```python
# Fetch published posts with pagination
from django.db.models import Count
from myapp.models import Post

# Optimized with prefetch_related
posts = Post.objects.filter(published=True).prefetch_related('author').order_by('-created_at')[0:10]

# Annotate with related count (e.g., comments)
from django.db.models import F
posts = Post.objects.annotate(comment_count=Count('comments', filter=Q(comments__is_read=False)))
```

---

### **3.2 API Endpoint Examples**
#### **Rails (REST API)**
```ruby
# routes.rb
resources :posts, only: [:index, :show, :create] do
  resources :comments, only: [:create]
end

# Controller (posts_controller.rb)
def create
  @post = Post.new(post_params)
  if @post.save
    render json: @post, status: :created
  else
    render json: @post.errors, status: :unprocessable_entity
  end
end
private
def post_params
  params.require(:post).permit(:title, :content)
end
```

#### **Django (DRF)**
```python
# models.py
from django.db import models
from django.contrib.auth.models import User

class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    published = models.BooleanField(default=False)

# serializers.py
from rest_framework import serializers
from .models import Post

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author']

# views.py
from rest_framework import generics
from .models import Post
from .serializers import PostSerializer

class PostListCreate(generics.ListCreateAPIView):
    queryset = Post.objects.filter(published=True)
    serializer_class = PostSerializer
```

---

### **3.3 Background Job Examples**
#### **Rails (Sidekiq)**
```ruby
# lib/jobs/send_email_job.rb
class SendEmailJob
  include Sidekiq::Job
  def perform(user_id, subject, body)
    user = User.find(user_id)
    UserMailer.welcome_email(user, subject, body).deliver_later
  end
end

# Enqueue in controller
SendEmailJob.perform_async(current_user.id, "Welcome", "Thanks for signing up!")
```

#### **Django (Celery)**
```python
# tasks.py
from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_welcome_email(user_id, subject, body):
    user = User.objects.get(id=user_id)
    send_mail(subject, body, 'noreply@example.com', [user.email])

# Enqueue in views.py
from .tasks import send_welcome_email
send_welcome_email.delay(user.id, "Welcome", "Thanks for joining!")
```

---

## **4. Implementation Best Practices**

### **4.1 Database Optimization**
- **Indexing**: Add indexes for frequently queried columns (e.g., `user.email`).
  ```ruby
  # Rails
  add_index :users, :email, unique: true

  # Django
  class User(models.Model):
      email = models.EmailField(unique=True, db_index=True)
  ```
- **Pagination**: Use `limit`/`offset` or libraries like `kaminari` (Rails) or `django-pagination`.
- **Connection Pooling**: Configure for high-traffic apps (e.g., `PG::ConnectionPool` in Rails).

### **4.2 Security**
- **Input Validation**: Use Rails’ strong parameters or Django’s form validation.
  ```ruby
  # Rails
  params.require(:user).permit(:email, :password) # Whitelist only allowed fields.

  # Django
  class UserForm(forms.ModelForm):
      class Meta:
          model = User
          fields = ['email', 'password']
          widgets = {'password': forms.PasswordInput}
  ```
- **CSRF Protection**: Enable in both frameworks (built-in in Django/Rails).
- **Rate Limiting**: Use `rack-attack` (Rails) or `django-ratelimit`.

### **4.3 Performance**
- **Caching**:
  - Rails: `Rails.cache.write(key, value, expires_in: 1.hour)`
  - Django: `cache.set('key', value, 3600)` (TTL in seconds).
- **Asset Compilation**: Use `webpacker` (Rails) or `django-compressor` (Django) for production.

### **4.4 Testing**
- **Unit Tests**:
  - Rails: `rspec` (e.g., `spec/models/post_spec.rb`).
  - Django: `pytest` + `django-test-plus`.
- **Integration Tests**: Simulate API calls:
  ```ruby
  # Rails (Capybara)
  it "creates a post" do
    visit new_post_path
    fill_in "Title", with: "Test Post"
    click_button "Create"
    expect(page).to have_content("Title")
  end

  # Django (LiveServerTestCase)
  from django.test import LiveServerTestCase
  class PostViewTest(LiveServerTestCase):
      def test_post_creation(self):
          response = self.client.post(
              reverse('post-create'),
              {'title': 'Test', 'content': 'Body'},
              follow=True
          )
          self.assertEqual(response.status_code, 200)
  ```

---

## **5. Related Patterns**
| **Pattern**               | **Description**                                                                 | **Rails/Django Tools**                          |
|---------------------------|-------------------------------------------------------------------------------|--------------------------------------------------|
| **Microservices**         | Decompose monoliths into modular services.                                    | Docker + Kubernetes, Rails API-only + Django.    |
| **GraphQL**               | Flexible querying over REST.                                                  | `graphql-ruby` (Rails), `django-graphql-jwt`.    |
| **Event-Driven Architecture** | Async communication via message queues.                                     | Sidekiq + Redis (Rails), Celery + RabbitMQ (Django). |
| **Serverless**            | Run functions on-demand (e.g., AWS Lambda).                                    | `rails-lambda`, Django + AWS Lambda Layers.     |
| **Headless CMS**          | Decouple content from backend (e.g., Strapi).                                | Strapi + Rails/Django APIs.                      |
| **Authentication**        | Secure user sessions with JWT/OAuth.                                          | `devise-jwt` (Rails), `django-allauth`.         |

---

## **6. Troubleshooting**
### **Common Issues & Fixes**
| **Issue**                          | **Rails Solution**                          | **Django Solution**                          |
|-------------------------------------|---------------------------------------------|----------------------------------------------|
| Slow DB queries                     | Add `EXPLAIN` to queries; use `bulk_insert`. | Use `django-debug-toolbar` for query profiling. |
| Memory leaks                        | Use `memory_profiler` gem.                  | Check with `django-debug-toolbar` memory tab. |
| Stale cache                         | Invalidate cache on write: `Rails.cache.delete(key)`. | Use `cache.invalidate_model(Post)`. |
| API rate limiting                   | `rack-attack` middleware.                   | `django-ratelimit` decorator.                |
| Deployment errors                   | Check `RAILS_ENV=production rails console`.  | `python manage.py runserver --settings=prod`. |

---

## **7. References**
- **Rails Guides**: [Rails API](https://guides.rubyonrails.org/api_app.html), [Testing](https://guides.rubyonrails.org/testing.html).
- **Django Docs**: [REST Framework](https://www.django-rest-framework.org/), [Testing](https://docs.djangoproject.com/en/stable/topics/testing/).
- **Performance**: [Rails Performance Guide](https://guides.rubyonrails.org/performance.html), [Django Best Practices](https://www.djangoproject.com/weblog/2017/jan/17/django-best-practices/).