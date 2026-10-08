import os
import time
import pytest
import threading
import logging
from unittest.mock import patch, MagicMock
from ai_engine.key_pool import GeminiKeyPool

# For testing, we create isolated pool instances to avoid global state pollution.

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEYS", "key1, key2,  key3, key2,,")
    monkeypatch.setenv("GEMINI_API_KEY", "legacy_key")
    
def test_initialization(mock_env):
    pool = GeminiKeyPool()
    assert pool.keys == ["key1", "key2", "key3"]
    assert pool.current_index == 0

def test_initialization_legacy_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEYS", "")
    monkeypatch.setenv("GEMINI_API_KEY", "legacy_key")
    pool = GeminiKeyPool()
    assert pool.keys == ["legacy_key"]

def test_execute_with_fallback_success(mock_env):
    pool = GeminiKeyPool()
    
    def dummy_func(key):
        return f"success with {key}"
        
    result = pool.execute_with_fallback(dummy_func)
    assert result == "success with key1"
    assert pool.current_index == 0

def test_execute_with_fallback_rate_limit(mock_env):
    pool = GeminiKeyPool()
    
    attempts = []
    def dummy_func(key):
        attempts.append(key)
        if key == "key1":
            raise Exception("Rate limit exceeded 429")
        return f"success with {key}"
        
    result = pool.execute_with_fallback(dummy_func)
    
    assert result == "success with key2"
    assert attempts == ["key1", "key2"]
    assert pool.current_index == 1
    assert 0 in pool.cooldowns

def test_execute_with_fallback_all_fail(mock_env):
    pool = GeminiKeyPool()
    
    attempts = []
    def dummy_func(key):
        attempts.append(key)
        raise Exception("RESOURCE_EXHAUSTED")
        
    with pytest.raises(RuntimeError, match="All configured Gemini API keys are currently unavailable."):
        pool.execute_with_fallback(dummy_func, max_retries=3)
        
    assert attempts == ["key1", "key2", "key3"]
    assert len(pool.cooldowns) == 3

def test_non_retryable_error(mock_env):
    pool = GeminiKeyPool()
    
    attempts = []
    def dummy_func(key):
        attempts.append(key)
        raise ValueError("Invalid request format")
        
    with pytest.raises(ValueError, match="Invalid request format"):
        pool.execute_with_fallback(dummy_func)
        
    assert attempts == ["key1"]
    assert len(pool.cooldowns) == 0

def test_cooldown_recovery(mock_env):
    pool = GeminiKeyPool()
    pool.transient_cooldown = 0.1
    pool.quota_cooldown = 0.2
    
    def dummy_func_fail(key):
        raise Exception("429 Rate Limit Exceeded")
        
    def dummy_func_success(key):
        return key

    with pytest.raises(RuntimeError):
        pool.execute_with_fallback(dummy_func_fail, max_retries=3)
        
    assert len(pool.cooldowns) == 3
    
    # Wait for transient recovery
    time.sleep(0.15)
    
    res2 = pool.execute_with_fallback(dummy_func_success)
    assert res2 in ["key1", "key2", "key3"]
    assert len(pool.cooldowns) == 0

def test_quota_cooldown(mock_env):
    pool = GeminiKeyPool()
    pool.transient_cooldown = 0.1
    pool.quota_cooldown = 2.0
    
    attempts = []
    def dummy_func(key):
        attempts.append(key)
        if key == "key1":
            raise Exception("Quota exceeded")
        return "success"
        
    res = pool.execute_with_fallback(dummy_func)
    assert res == "success"
    assert attempts == ["key1", "key2"]
    
    # key1 should be in long cooldown
    assert len(pool.cooldowns) == 1
    
    time.sleep(0.15)
    # still in cooldown
    assert len(pool.cooldowns) == 1
    
    pool.cooldowns.clear() # clear for test speed

def test_concurrent_access(mock_env):
    pool = GeminiKeyPool()
    
    results = []
    def thread_func():
        def dummy_func(key):
            time.sleep(0.01)
            return key
        results.append(pool.execute_with_fallback(dummy_func))
        
    threads = [threading.Thread(target=thread_func) for _ in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()
    
    assert len(results) == 10
    assert all(r == "key1" for r in results)

def test_no_keys_in_logs(caplog, mock_env):
    caplog.set_level(logging.DEBUG, logger="interviewmind.ai_engine.key_pool")
    pool = GeminiKeyPool()
    
    def dummy_func(key):
        if key == "key1":
            raise Exception("429")
        return "success"
        
    pool.execute_with_fallback(dummy_func)
    
    logs = caplog.text
    assert "key1" not in logs
    assert "key2" not in logs

def test_transient_cooldown_loop_no_deadlock(mock_env, monkeypatch):
    # Test that transient cooldown loop doesn't deadlock and wakes up
    pool = GeminiKeyPool()
    
    # We want to mock time.sleep so we don't actually wait 60s
    sleep_calls = []
    def mock_sleep(seconds):
        sleep_calls.append(seconds)
        # Fast forward time manually by clearing the cooldowns
        # so the next iteration of the while loop succeeds
        pool.cooldowns.clear()
        
    monkeypatch.setattr(time, "sleep", mock_sleep)
    
    # Mocking all keys to fail once with 429 to trigger transient cooldown
    attempts = []
    def dummy_func(key):
        attempts.append(key)
        # If it's the first time we see this key, raise 429
        if attempts.count(key) == 1:
            raise Exception("429 Too Many Requests")
        return "success"
        
    result = pool.execute_with_fallback(dummy_func)
    
    # Verify result
    assert result == "success"
    
    # Verify sleep was called once for the max transient duration
    assert len(sleep_calls) == 1
    # Because there are 3 keys, each gets marked with ~60s transient cooldown.
    assert sleep_calls[0] > 0
    
    # Verify that it attempted key1, key2, key3, and then retried key1
    assert len(attempts) == 4
    assert attempts[0] == "key1"
    assert attempts[1] == "key2"
    assert attempts[2] == "key3"
    assert attempts[3] == "key3"

def test_classification_rpm_vs_quota():
    pool = GeminiKeyPool()
    
    # A. RPM 429
    assert pool.classify_error(Exception("Quota exceeded for quota metric 'Generate Content API requests per minute'")) == "TRANSIENT"
    assert pool.classify_error(Exception("429 Too Many Requests")) == "TRANSIENT"
    
    # B. Genuine hard/daily quota
    assert pool.classify_error(Exception("Quota exceeded for quota metric 'Generate Content API requests per day'")) == "QUOTA"
    assert pool.classify_error(Exception("You have exceeded your quota.")) == "QUOTA"

def test_all_keys_hard_quota(mock_env, monkeypatch):
    pool = GeminiKeyPool()
    pool.quota_cooldown = 86400
    
    # Should not sleep
    sleep_calls = []
    monkeypatch.setattr(time, "sleep", lambda s: sleep_calls.append(s))
    
    attempts = []
    def dummy_func(key):
        attempts.append(key)
        raise Exception("requests per day") # Hard quota
        
    # C. All keys hard-quota exhausted -> exits cleanly by propagating RuntimeError
    with pytest.raises(RuntimeError, match="All configured Gemini API keys are currently unavailable."):
        pool.execute_with_fallback(dummy_func)
        
    # Attempted all 3 keys
    assert attempts == ["key1", "key2", "key3"]
    # No sleeps, because it's a hard quota
    assert len(sleep_calls) == 0

def test_mixed_key_pool_states(mock_env, monkeypatch):
    pool = GeminiKeyPool()
    
    # E. Mixed situation
    attempts = []
    def dummy_func(key):
        attempts.append(key)
        if key == "key1":
            raise Exception("requests per day") # Hard quota
        if key == "key2":
            raise Exception("requests per minute") # Transient
        return "success"
        
    result = pool.execute_with_fallback(dummy_func)
    
    # Result should be success from key3
    assert result == "success"
    
    # Key1 -> hard, Key2 -> transient, Key3 -> success
    assert attempts == ["key1", "key2", "key3"]
    
    # Verify cooldowns
    assert len(pool.cooldowns) == 2
    assert pool.cooldowns[0] > time.time() + 80000 # key1 hard quota
    assert pool.cooldowns[1] < time.time() + 300 # key2 transient
