import pytest
import time
import logging
from unittest.mock import patch, MagicMock

from ai_engine.key_pool import GeminiKeyPool

class TestGeminiKeyPoolDetailed:

    @pytest.fixture
    def pool(self):
        p = GeminiKeyPool()
        p.keys = ["key_A", "key_B", "key_C"]
        p.cooldowns = {}
        p.current_index = 0
        return p

    def test_healthy_key_execution(self, pool):
        mock_func = MagicMock(return_value="success")
        res = pool.execute_with_fallback(mock_func)
        assert res == "success"
        assert len(pool.cooldowns) == 0

    def test_invalid_key_401(self, pool):
        mock_func = MagicMock()
        mock_func.side_effect = [Exception("401 Unauthorized"), "success"]
        res = pool.execute_with_fallback(mock_func)
        assert res == "success"
        # 401 should trigger transient failover
        assert 0 in pool.cooldowns

    def test_quota_rate_limit_429(self, pool):
        mock_func = MagicMock()
        mock_func.side_effect = [Exception("429 Too Many Requests"), "success"]
        res = pool.execute_with_fallback(mock_func)
        assert res == "success"
        assert 0 in pool.cooldowns

    def test_temporary_failure_503(self, pool):
        mock_func = MagicMock()
        mock_func.side_effect = [Exception("503 Service Unavailable"), "success"]
        res = pool.execute_with_fallback(mock_func)
        assert res == "success"
        assert 0 in pool.cooldowns

    def test_timeout_504(self, pool):
        mock_func = MagicMock()
        mock_func.side_effect = [TimeoutError("timeout"), "success"]
        res = pool.execute_with_fallback(mock_func)
        assert res == "success"
        assert 0 in pool.cooldowns

    def test_multiple_keys_rotation(self, pool):
        mock_func = MagicMock()
        mock_func.side_effect = [Exception("429"), Exception("429"), "success"]
        res = pool.execute_with_fallback(mock_func)
        assert res == "success"
        assert 0 in pool.cooldowns
        assert 1 in pool.cooldowns
        assert 2 not in pool.cooldowns

    def test_one_bad_key_several_healthy(self, pool):
        mock_func = MagicMock()
        mock_func.side_effect = [Exception("401"), "success", "success2"]
        
        res1 = pool.execute_with_fallback(mock_func)
        assert res1 == "success"
        
        # Second execution should use the next healthy key directly without failing
        # because the first one is still on cooldown
        res2 = pool.execute_with_fallback(mock_func)
        assert res2 == "success2"
        assert 0 in pool.cooldowns

    def test_all_keys_unavailable(self, pool):
        mock_func = MagicMock()
        mock_func.side_effect = [Exception("429"), Exception("429"), Exception("429")]
        
        with pytest.raises(RuntimeError) as excinfo:
            pool.execute_with_fallback(mock_func, fail_fast=True)
            
        assert "All configured Gemini API keys are currently unavailable" in str(excinfo.value)
        assert len(pool.cooldowns) == 3

    def test_keys_are_never_printed_in_logs(self, pool, caplog):
        caplog.set_level(logging.WARNING)
        mock_func = MagicMock()
        mock_func.side_effect = [Exception("429 Too Many Requests"), "success"]
        
        pool.execute_with_fallback(mock_func)
        
        # Verify that logs do not contain the actual keys
        for record in caplog.records:
            assert "key_A" not in record.message
            assert "key_B" not in record.message
            assert "key_C" not in record.message
            assert "key index" in record.message

    def test_key_rotation_behavior_safe(self, pool):
        # A test to ensure we don't accidentally get stuck rotating forever
        pool.keys = ["key_A"] # Only one key
        mock_func = MagicMock()
        mock_func.side_effect = [Exception("429"), Exception("429")]
        
        with pytest.raises(RuntimeError):
            pool.execute_with_fallback(mock_func, max_retries=1)
            
        assert 0 in pool.cooldowns
