# frozen_string_literal: true

require_relative 'test_helper'

class SecurityRateLimitTest < Minitest::Test
  def setup
    @factory = TestFactory.new
    @rate_limiter = RateLimiter.new
  end

  def teardown
    @factory.reset
    @rate_limiter.reset
  end

  # ============================================================================
  # Per-User Rate Limiting Tests
  # ============================================================================

  def test_allows_requests_within_rate_limit
    # Arrange
    user = @factory.create_user('alice', 'alice@example.com', 'Alice')
    max_requests = 5

    # Act - make 5 requests (within limit)
    results = []
    max_requests.times do
      results << @rate_limiter.check_rate_limit(user[:id], limit: 10, window: 60)
    end

    # Assert - all requests should be allowed
    assert results.all?, 'All requests within rate limit should be allowed'
  end

  def test_blocks_requests_exceeding_rate_limit
    # Arrange
    user = @factory.create_user('alice', 'alice@example.com', 'Alice')
    max_requests = 10

    # Act - make 10 requests at the limit
    max_requests.times do
      @rate_limiter.check_rate_limit(user[:id], limit: max_requests, window: 60)
    end

    # Act - attempt 11th request (should be blocked)
    result = @rate_limiter.check_rate_limit(user[:id], limit: max_requests, window: 60)

    # Assert - 11th request should be blocked
    refute result, 'Request exceeding rate limit should be blocked'
  end

  def test_rate_limit_window_reset
    # Arrange
    user = @factory.create_user('alice', 'alice@example.com', 'Alice')
    max_requests = 5
    window_seconds = 2

    # Act - exhaust rate limit
    max_requests.times do
      @rate_limiter.check_rate_limit(user[:id], limit: max_requests, window: window_seconds)
    end

    # Assert - next request should be blocked
    refute @rate_limiter.check_rate_limit(user[:id], limit: max_requests, window: window_seconds)

    # Act - wait for window to reset
    sleep(window_seconds + 0.1)

    # Assert - request should be allowed after window reset
    assert @rate_limiter.check_rate_limit(user[:id], limit: max_requests, window: window_seconds),
           'Requests should be allowed after rate limit window reset'
  end

  def test_independent_rate_limits_per_user
    # Arrange
    user1 = @factory.create_user('alice', 'alice@example.com', 'Alice')
    user2 = @factory.create_user('bob', 'bob@example.com', 'Bob')
    max_requests = 3

    # Act - user1 exhausts their rate limit
    max_requests.times do
      @rate_limiter.check_rate_limit(user1[:id], limit: max_requests, window: 60)
    end

    # Assert - user1 is blocked
    refute @rate_limiter.check_rate_limit(user1[:id], limit: max_requests, window: 60)

    # Assert - user2 should still be allowed
    assert @rate_limiter.check_rate_limit(user2[:id], limit: max_requests, window: 60),
           'Different users should have independent rate limits'
  end

  def test_rate_limit_by_ip_address
    # Arrange
    ip_address_1 = '192.168.1.100'
    ip_address_2 = '192.168.1.101'
    max_requests = 5

    # Act - exhaust rate limit for IP 1
    max_requests.times do
      @rate_limiter.check_rate_limit(ip_address_1, limit: max_requests, window: 60)
    end

    # Assert - IP 1 is blocked
    refute @rate_limiter.check_rate_limit(ip_address_1, limit: max_requests, window: 60)

    # Assert - IP 2 should still be allowed
    assert @rate_limiter.check_rate_limit(ip_address_2, limit: max_requests, window: 60),
           'Different IP addresses should have independent rate limits'
  end

  # ============================================================================
  # Different Rate Limits for Different Actions
  # ============================================================================

  def test_different_limits_for_read_vs_write_operations
    # Arrange
    user = @factory.create_user('alice', 'alice@example.com', 'Alice')
    read_limit = 100
    write_limit = 10

    # Act - exhaust write limit
    write_limit.times do
      @rate_limiter.check_rate_limit("#{user[:id]}:write", limit: write_limit, window: 60)
    end

    # Assert - write operations should be blocked
    refute @rate_limiter.check_rate_limit("#{user[:id]}:write", limit: write_limit, window: 60)

    # Assert - read operations should still be allowed
    assert @rate_limiter.check_rate_limit("#{user[:id]}:read", limit: read_limit, window: 60),
           'Read operations should have separate rate limit from write operations'
  end

  def test_stricter_limit_for_expensive_operations
    # Arrange
    user = @factory.create_user('alice', 'alice@example.com', 'Alice')
    expensive_op_limit = 2

    # Act - exhaust expensive operation limit
    expensive_op_limit.times do
      @rate_limiter.check_rate_limit("#{user[:id]}:expensive", limit: expensive_op_limit, window: 60)
    end

    # Assert - expensive operation should be blocked
    refute @rate_limiter.check_rate_limit("#{user[:id]}:expensive", limit: expensive_op_limit, window: 60),
           'Expensive operations should have stricter rate limits'
  end

  # ============================================================================
  # Rate Limit Headers and Response Tests
  # ============================================================================

  def test_returns_remaining_requests_count
    # Arrange
    user = @factory.create_user('alice', 'alice@example.com', 'Alice')
    max_requests = 10
    requests_made = 3

    # Act - make 3 requests
    requests_made.times do
      @rate_limiter.check_rate_limit(user[:id], limit: max_requests, window: 60)
    end

    # Get remaining count
    remaining = @rate_limiter.get_remaining(user[:id], limit: max_requests)

    # Assert - should have 7 remaining
    assert_equal (max_requests - requests_made), remaining
  end

  def test_returns_rate_limit_reset_time
    # Arrange
    user = @factory.create_user('alice', 'alice@example.com', 'Alice')
    window_seconds = 60

    # Act - make a request
    @rate_limiter.check_rate_limit(user[:id], limit: 10, window: window_seconds)

    # Get reset time
    reset_time = @rate_limiter.get_reset_time(user[:id])

    # Assert - reset time should be in the future
    assert reset_time > Time.now
    assert reset_time <= (Time.now + window_seconds)
  end

  # ============================================================================
  # Edge Cases and Security Tests
  # ============================================================================

  def test_handles_burst_traffic
    # Arrange
    user = @factory.create_user('alice', 'alice@example.com', 'Alice')
    max_requests = 10

    # Act - make rapid concurrent requests
    results = []
    threads = []
    20.times do
      threads << Thread.new do
        results << @rate_limiter.check_rate_limit(user[:id], limit: max_requests, window: 60)
      end
    end
    threads.each(&:join)

    # Assert - only max_requests should be allowed
    allowed_count = results.count(true)
    assert allowed_count <= max_requests, "Only #{max_requests} requests should be allowed, got #{allowed_count}"
  end

  def test_prevents_rate_limit_bypass_with_multiple_identifiers
    # Arrange
    user = @factory.create_user('alice', 'alice@example.com', 'Alice')
    max_requests = 5

    # Act - exhaust rate limit with user ID
    max_requests.times do
      @rate_limiter.check_rate_limit(user[:id], limit: max_requests, window: 60)
    end

    # Assert - cannot bypass with slightly modified identifier
    refute @rate_limiter.check_rate_limit(user[:id], limit: max_requests, window: 60)
    refute @rate_limiter.check_rate_limit("#{user[:id]} ", limit: max_requests, window: 60),
           'Should not bypass rate limit with whitespace'
    refute @rate_limiter.check_rate_limit(user[:id].upcase, limit: max_requests, window: 60),
           'Should not bypass rate limit with case change'
  end

  def test_handles_missing_user_identifier
    # Act & Assert - should not raise error
    assert_raises(ArgumentError) do
      @rate_limiter.check_rate_limit(nil, limit: 10, window: 60)
    end
  end

  # ============================================================================
  # Helper Class: Simple Rate Limiter Implementation
  # ============================================================================

  class RateLimiter
    def initialize
      @requests = {}
    end

    def check_rate_limit(identifier, limit:, window:)
      raise ArgumentError, 'Identifier cannot be nil' if identifier.nil?

      # Normalize identifier (trim whitespace, lowercase)
      key = identifier.to_s.strip.downcase

      now = Time.now.to_f
      @requests[key] ||= []

      # Remove expired requests outside the window
      @requests[key].reject! { |timestamp| timestamp < (now - window) }

      # Check if under limit
      if @requests[key].length < limit
        @requests[key] << now
        true
      else
        false
      end
    end

    def get_remaining(identifier, limit:)
      key = identifier.to_s.strip.downcase
      @requests[key] ||= []
      [limit - @requests[key].length, 0].max
    end

    def get_reset_time(identifier)
      key = identifier.to_s.strip.downcase
      @requests[key] ||= []
      return Time.now if @requests[key].empty?

      # Reset time is when the oldest request expires
      oldest_request = @requests[key].min
      Time.at(oldest_request + 60) # Assuming 60 second window
    end

    def reset
      @requests.clear
    end
  end
end
