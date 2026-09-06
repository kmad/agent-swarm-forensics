"""The read-only control must fail closed before any evidence-key request."""
import contextlib
import importlib.util
import io
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('verify_live', Path(__file__).resolve().parents[1] / 'scripts/verify_live.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
MISSING = (404, '{"error":"Key not found"}', {})


class CounterGuardTests(unittest.TestCase):
    def test_each_control_failure_stops_before_signal_reads(self):
        for position in range(3):
            for bad in [(200, '{"value":0}', {}), (503, 'unavailable', {}), (200, '[]', {}), (200, 'Key not found', {})]:
                with self.subTest(position=position, response=bad), patch.object(probe, 'get', side_effect=[MISSING] * position + [bad]) as get, contextlib.redirect_stdout(io.StringIO()):
                    self.assertFalse(probe.probe_counters(False))
                    self.assertEqual(get.call_count, position + 1)
                    self.assertTrue(all('forensics_read_control_' in call.args[0] for call in get.call_args_list))

    def test_passing_controls_allow_read_endpoints_only(self):
        def fake_get(url):
            self.assertIn('/api/v1/get/', url)
            self.assertIn('?audit=', url)
            if 'forensics_read_control_' in url:
                return MISSING
            return (200, '{"value":1}', {})
        with patch.object(probe, 'get', side_effect=fake_get) as get, contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(probe.probe_counters(False))
            self.assertEqual(get.call_count, 3 + len(probe.COUNTER_BASELINE))

    def test_main_does_not_continue_after_failed_control(self):
        with patch('sys.argv', ['verify_live.py']), patch.object(probe, 'probe_counters', return_value=False), patch.object(probe, 'probe_httpbin') as next_probe, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(probe.main(), 1)
            next_probe.assert_not_called()


if __name__ == '__main__':
    unittest.main()
