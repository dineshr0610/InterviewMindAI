import pytest
import time
from unittest.mock import patch, MagicMock

from ai_engine.key_pool import GeminiKeyPool

class TestGeminiKeyPool:

    @pytest.fixture
    def mock_key_pool(self):
        pool = GeminiKeyPool()
        pool.keys = ["key1", "key2", "key3"]
        pool.cooldowns = {}
        pool.current_index = 0
        return pool

    def test_classify_error_429_transient(self, mock_key_pool):
        err = Exception("429 Too Many Requests")
        assert mock_key_pool.classify_error(err) == "TRANSIENT"

    def test_classify_error_503(self, mock_key_pool):
        err = Exception("503 Service Unavailable")
        assert mock_key_pool.classify_error(err) == "UNAVAILABLE"

    def test_classify_error_504(self, mock_key_pool):
        err = Exception("504 DEADLINE_EXCEEDED")
        assert mock_key_pool.classify_error(err) == "TIMEOUT"
        
        err2 = TimeoutError("timeout")
        assert mock_key_pool.classify_error(err2) == "TIMEOUT"

    def test_classify_error_hard_quota(self, mock_key_pool):
        err = Exception("GenerateRequestsPerDayPerProjectPerModel-FreeTier")
        assert mock_key_pool.classify_error(err) == "QUOTA"

    def test_failover_transient(self, mock_key_pool):
        mock_func = MagicMock()
        mock_func.side_effect = [Exception("429"), "success"]
        
        res = mock_key_pool.execute_with_fallback(mock_func)
        assert res == "success"
        assert len(mock_key_pool.cooldowns) == 1
        assert 0 in mock_key_pool.cooldowns

    def test_failover_504_then_success(self, mock_key_pool):
        mock_func = MagicMock()
        mock_func.side_effect = [TimeoutError("timeout"), "success"]
        
        res = mock_key_pool.execute_with_fallback(mock_func)
        assert res == "success"
        assert len(mock_key_pool.cooldowns) == 1
        assert 0 in mock_key_pool.cooldowns

    def test_failover_all_keys_fail_504(self, mock_key_pool):
        mock_func = MagicMock()
        mock_func.side_effect = [TimeoutError("timeout"), Exception("504"), TimeoutError("timeout")]
        
        with pytest.raises(RuntimeError):
            mock_key_pool.execute_with_fallback(mock_func, max_retries=3)
            
        assert len(mock_key_pool.cooldowns) == 3

    def test_failover_quota_cooldown(self, mock_key_pool):
        mock_func = MagicMock()
        mock_func.side_effect = [Exception("requests per day quota"), "success"]
        
        res = mock_key_pool.execute_with_fallback(mock_func)
        assert res == "success"
        assert 0 in mock_key_pool.cooldowns
        # Verify quota cooldown is larger
        cooldown_time = mock_key_pool.cooldowns[0] - time.time()
        assert cooldown_time > 1000 # Should be 86400

    def test_failover_504_cooldown(self, mock_key_pool):
        mock_func = MagicMock()
        mock_func.side_effect = [Exception("504"), "success"]
        
        res = mock_key_pool.execute_with_fallback(mock_func)
        assert res == "success"
        assert 0 in mock_key_pool.cooldowns
        # Verify 504 cooldown is short
        cooldown_time = mock_key_pool.cooldowns[0] - time.time()
        assert cooldown_time <= 10 # Should be 10

