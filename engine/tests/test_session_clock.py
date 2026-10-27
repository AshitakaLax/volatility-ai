"""engine/trading/session_clock.py: the day's real close from Alpaca's calendar."""

from __future__ import annotations

from datetime import date, datetime, time
from types import SimpleNamespace

from engine.trading.session_clock import alpaca_close_for


class _Client:
    def __init__(self, days):
        self.days, self.asked = days, []

    def get_calendar(self, request):
        self.asked.append(request.start)
        return [d for d in self.days if d.date == request.start]


def test_an_early_close_comes_from_the_calendar_and_is_asked_once():
    black_friday = date(2026, 11, 27)
    client = _Client([SimpleNamespace(date=black_friday, close=time(13, 0))])
    close_for = alpaca_close_for(client)
    assert close_for(black_friday) == time(13, 0)
    assert close_for(black_friday) == time(13, 0)
    assert client.asked == [black_friday]


def test_a_day_the_calendar_does_not_list_has_no_session():
    assert alpaca_close_for(_Client([]))(date(2026, 11, 26)) is None


def test_a_datetime_close_is_read_as_its_time():
    day = date(2026, 10, 27)
    client = _Client(
        [SimpleNamespace(date=datetime(2026, 10, 27), close=datetime(2026, 10, 27, 16))]
    )
    client.days[0].date = day
    assert alpaca_close_for(client)(day) == time(16, 0)


def test_an_unreadable_calendar_falls_back_to_the_holiday_rules():
    class Broken:
        def get_calendar(self, request):
            raise ConnectionError("down")

    close_for = alpaca_close_for(Broken())
    assert close_for(date(2026, 10, 27)) == time(16, 0)
    assert close_for(date(2026, 11, 26)) is None, "Thanksgiving, by the rules"
