from unittest.mock import MagicMock, patch

from app.tasks.scheduler import start_scheduler, stop_scheduler


class TestScheduler:
    @patch("app.tasks.scheduler.scheduler")
    def test_start_scheduler_adds_job(self, mock_scheduler):
        start_scheduler()

        mock_scheduler.add_job.assert_called_once()
        call_kwargs = mock_scheduler.add_job.call_args
        assert call_kwargs[0][1] == "interval"
        assert call_kwargs[1]["hours"] == 1
        assert call_kwargs[1]["id"] == "scrape_tracked_products"
        mock_scheduler.start.assert_called_once()

    @patch("app.tasks.scheduler.scheduler")
    def test_stop_scheduler(self, mock_scheduler):
        stop_scheduler()
        mock_scheduler.shutdown.assert_called_once()
