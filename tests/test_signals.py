import unittest
from datetime import date

from app.domain import Checkin, Checkpoint, bucket, collect_signals


def point(code, offset, kind="task", done=False, owner="manager", title=""):
    return Checkpoint(
        id=offset,
        code=code,
        day_offset=offset,
        title=title or code,
        detail="",
        owner=owner,
        kind=kind,
        done=done,
        result="",
    )


class CollectSignalsTests(unittest.TestCase):
    def test_overdue_task_is_risk(self):
        start = date(2026, 11, 1)
        today = date(2026, 11, 11)
        signals = collect_signals(today, start, [point("access", 1, title="Доступы")], [])
        self.assertEqual(signals[0].tone, "risk")
        self.assertIn("Доступы", signals[0].text)
        self.assertEqual(bucket(signals), "act")

    def test_future_task_is_silent(self):
        start = date(2026, 11, 10)
        today = date(2026, 11, 11)
        signals = collect_signals(today, start, [point("solo", 7, title="Допуск")], [])
        self.assertEqual(signals, [])
        self.assertEqual(bucket(signals), "ok")

    def test_task_due_today_is_not_overdue(self):
        start = date(2026, 11, 10)
        today = date(2026, 11, 11)
        signals = collect_signals(today, start, [point("catalog", 1, title="Прайс")], [])
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].tone, "today")
        self.assertEqual(bucket(signals), "today")

    def test_missing_checkin_after_due_day(self):
        start = date(2026, 10, 1)
        today = date(2026, 10, 20)
        signals = collect_signals(
            today,
            start,
            [point("checkin_14", 14, kind="checkin", title="Разговор")],
            [],
        )
        self.assertEqual(signals[0].tone, "risk")
        self.assertIn("просрочен", signals[0].text)

    def test_checkin_due_today_is_risk(self):
        start = date(2026, 10, 28)
        today = date(2026, 11, 11)
        signals = collect_signals(
            today,
            start,
            [point("checkin_14", 14, kind="checkin")],
            [],
        )
        self.assertIn("сегодня", signals[0].text)

    def test_negative_checkin_stays_until_resolved(self):
        start = date(2026, 10, 1)
        today = date(2026, 11, 11)
        checkin = Checkin(14, "yes", "no", "unsure", "", False, "")
        signals = collect_signals(
            today,
            start,
            [point("checkin_14", 14, kind="checkin", done=True)],
            [checkin],
        )
        self.assertEqual(signals[0].tone, "risk")
        self.assertIn("не знает, к кому идти", signals[0].text)
        self.assertIn("сомневается", signals[0].text)

    def test_resolved_negative_checkin_is_silent(self):
        start = date(2026, 10, 1)
        today = date(2026, 11, 11)
        checkin = Checkin(14, "no", "no", "no", "", True, "Передал клиентов")
        signals = collect_signals(
            today,
            start,
            [point("checkin_14", 14, kind="checkin", done=True)],
            [checkin],
        )
        self.assertEqual(signals, [])

    def test_positive_checkin_is_silent(self):
        start = date(2026, 10, 1)
        today = date(2026, 11, 11)
        checkin = Checkin(14, "yes", "yes", "yes", "", False, "")
        signals = collect_signals(
            today,
            start,
            [point("checkin_14", 14, kind="checkin", done=True)],
            [checkin],
        )
        self.assertEqual(signals, [])

    def test_partly_understands_is_a_signal(self):
        checkin = Checkin(14, "partly", "yes", "yes", "", False, "")
        signals = collect_signals(
            date(2026, 11, 11),
            date(2026, 10, 1),
            [point("checkin_14", 14, kind="checkin", done=True)],
            [checkin],
        )
        self.assertIn("частично", signals[0].text)

    def test_decision_due_today(self):
        start = date(2026, 8, 13)
        today = date(2026, 11, 11)
        signals = collect_signals(
            today,
            start,
            [point("decision_90", 90, kind="decision", title="Решение")],
            [],
        )
        self.assertEqual(signals[0].tone, "decision")
        self.assertEqual(bucket(signals), "act")

    def test_done_decision_is_silent(self):
        signals = collect_signals(
            date(2026, 11, 11),
            date(2026, 8, 13),
            [point("decision_90", 90, kind="decision", done=True)],
            [],
        )
        self.assertEqual(signals, [])

    def test_risk_outranks_today(self):
        start = date(2026, 11, 8)
        today = date(2026, 11, 11)
        signals = collect_signals(
            today,
            start,
            [
                point("buddy", 0, title="Наставник"),
                point("routes", 3, title="Маршруты"),
            ],
            [],
        )
        self.assertEqual(signals[0].tone, "risk")
        self.assertEqual(bucket(signals), "act")


if __name__ == "__main__":
    unittest.main()
