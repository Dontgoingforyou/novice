import os
import tempfile
import unittest
from datetime import date, timedelta

fd, DB = tempfile.mkstemp(suffix=".sqlite")
os.close(fd)
os.environ["NOVICE_DB"] = DB

from fastapi.testclient import TestClient  # noqa: E402

from app import db  # noqa: E402
from app.main import app  # noqa: E402


def person_id(name: str) -> int:
    with db.connect() as conn:
        db.init_db(conn)
        row = conn.execute("SELECT id FROM people WHERE name = ?", (name,)).fetchone()
    return int(row["id"])


def decision_id(name: str) -> int:
    with db.connect() as conn:
        row = conn.execute(
            """
            SELECT checkpoints.id AS id
            FROM checkpoints
            JOIN people ON people.id = checkpoints.person_id
            WHERE people.name = ? AND checkpoints.kind = 'decision'
            """,
            (name,),
        ).fetchone()
    return int(row["id"])


class FlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        os.remove(DB)

    def test_olga_board_shows_who_to_open_today(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        text = response.text
        self.assertIn("Ольга Семёнова", text)
        self.assertIn("Тимур Сафин", text)
        self.assertIn("Софья Ильина", text)
        self.assertIn("Кира Лебедева", text)
        self.assertIn("Разобрать сейчас", text)
        self.assertIn("Идут по плану", text)
        # Кира спокойная, Тимур и Софья — в первом блоке. Проверяем порядок карточек.
        self.assertLess(text.index("Тимур Сафин"), text.index("Идут по плану"))
        self.assertLess(text.index("Софья Ильина"), text.index("Кира Лебедева"))

    def test_timur_checkin_clears_the_signal(self):
        timur = person_id("Тимур Сафин")
        page = self.client.get(f"/p/{timur}")
        self.assertIn("45-й день просрочен", page.text)
        saved = self.client.post(
            f"/p/{timur}/checkins/45",
            data={"understands": "yes", "knows_who": "yes", "wants_stay": "yes", "note": "Смена стабильная"},
            follow_redirects=True,
        )
        self.assertEqual(saved.status_code, 200)
        self.assertIn("На доске тихо", saved.text)
        self.assertNotIn("просрочен", saved.text)

    def test_sofya_decision_is_recorded(self):
        sofya = person_id("Софья Ильина")
        saved = self.client.post(
            f"/p/{sofya}/checkpoints/{decision_id('Софья Ильина')}/decision",
            data={"result": "stay"},
            follow_redirects=True,
        )
        self.assertIn("Остаётся", saved.text)
        self.assertNotIn("Решение на 90-й день: сегодня", saved.text)

    def test_alina_gets_a_named_buddy(self):
        alina = person_id("Алина Мороз")
        page = self.client.get(f"/p/{alina}")
        self.assertIn("Наставник не назначен", page.text)
        self.assertIn("Доступы", page.text)
        saved = self.client.post(
            f"/p/{alina}/buddy",
            data={"buddy_name": "Вера Логинова"},
            follow_redirects=True,
        )
        self.assertIn("Вера Логинова", saved.text)
        self.assertIn("Просрочено: Доступы", saved.text)

    def test_new_person_without_buddy_lands_on_the_board(self):
        created = self.client.post(
            "/new",
            data={
                "name": "Ян Котов",
                "role": "seller",
                "place": "Магазин «Север»",
                "start_date": (date.today() - timedelta(days=3)).isoformat(),
                "manager": "Ольга Семёнова",
                "buddy": "",
            },
            follow_redirects=True,
        )
        self.assertEqual(created.status_code, 200)
        self.assertIn("Ян Котов", created.text)
        self.assertIn("Назначить наставника", created.text)
        board = self.client.get("/?manager=Ольга%20Семёнова")
        self.assertIn("Ян Котов", board.text)
        self.assertIn("Разобрать", board.text)

    def test_newcomer_page_does_not_ask_for_a_future_decision(self):
        kira = person_id("Кира Лебедева")
        page = self.client.get(f"/p/{kira}/my")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Нина Волкова", page.text)
        self.assertNotIn("Решение на 90-й день", page.text)

    def test_empty_name_is_rejected(self):
        response = self.client.post(
            "/new",
            data={"name": "  ", "role": "office", "place": "Офис", "start_date": "2026-11-11", "manager": "Алексей Берестов"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Нужны имя", response.text)


if __name__ == "__main__":
    unittest.main()
