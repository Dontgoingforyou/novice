"""План на 90 дней и правила, по которым карточка попадает на доску."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

OWNERS = {
    "manager": "Руководитель",
    "buddy": "Наставник",
    "newcomer": "Новичок",
}

ROLES: dict[str, dict] = {
    "seller": {
        "label": "Продавец магазина",
        "hint": "Учебный чек, первая смена с наставником, допуск в зал.",
        "points": [
            ("buddy", 0, "manager", "task", "Назначить наставника", "Без имени наставника первая неделя не начинается."),
            ("uniform", 1, "newcomer", "task", "Форма, пропуск, учебный режим кассы", "Пока касса в учебном режиме, живые чеки не пробивает."),
            ("first_shift", 1, "buddy", "task", "Первая смена вместе", "Зал, примерочные, где что лежит, как звать старшего."),
            ("training_receipt", 3, "newcomer", "task", "Учебный чек и возврат", "Под присмотром наставника, не в час пик."),
            ("solo_permit", 7, "manager", "task", "Допуск к самостоятельной смене", "Либо выходит один, либо честно ещё неделя с наставником."),
            ("checkin_14", 14, "manager", "checkin", "Разговор на 14-й день", "Понимает ли, чего ждут, знает ли, к кому идти, хочет ли остаться."),
            ("solo_review", 30, "manager", "task", "Смена без наставника", "Разобрать два реальных диалога с покупателем."),
            ("checkin_45", 45, "manager", "checkin", "Разговор на 45-й день", "Повторный пульс: до трёх месяцев ещё есть время успеть."),
            ("quality_60", 60, "manager", "task", "Возвраты и недостачи", "Норма за месяц или короткий план, без общего «молодец»."),
            ("decision_90", 90, "manager", "decision", "Решение на 90-й день", "Остаётся, ещё месяц с планом или расстаёмся."),
        ],
    },
    "warehouse": {
        "label": "Кладовщик",
        "hint": "Техника безопасности, первая сборка в WMS, допуск к самостоятельному заказу.",
        "points": [
            ("buddy", 0, "manager", "task", "Назначить наставника", "На смене должен быть конкретный человек, не «спросите на складе»."),
            ("safety", 1, "newcomer", "task", "Техника безопасности и зоны", "Рохля, зоны, чего не делать одному."),
            ("first_pick", 2, "buddy", "task", "Первая сборка в WMS", "Вместе с наставником, с разбором пересорта."),
            ("inbound", 5, "buddy", "task", "Приёмка поставки вместе", "Расхождения не прячем, показываем как фиксировать."),
            ("solo_pick", 7, "manager", "task", "Допуск к мелкому заказу", "Сам собирает небольшой заказ, наставник проверяет."),
            ("checkin_14", 14, "manager", "checkin", "Разговор на 14-й день", "Понимает ли смену, знает ли, к кому идти, хочет ли остаться."),
            ("pick_rate", 30, "manager", "task", "Норма сборки без пересорта", "Цифра за неделю, не ощущение «вроде справляется»."),
            ("checkin_45", 45, "manager", "checkin", "Разговор на 45-й день", "Повторный пульс до конца третьего месяца."),
            ("inventory", 60, "manager", "task", "Ошибки на инвентаризации", "Что перепутал и повторяется ли это."),
            ("decision_90", 90, "manager", "decision", "Решение на 90-й день", "Остаётся, ещё месяц с планом или расстаёмся."),
        ],
    },
    "wholesale": {
        "label": "Менеджер опта",
        "hint": "Слушает живые звонки, первый звонок сам, десять своих клиентов.",
        "points": [
            ("buddy", 0, "manager", "task", "Назначить наставника", "Старший менеджер, который реально отдаст часть клиентов."),
            ("catalog", 1, "newcomer", "task", "Бренды, наличие, чем наш прайс отличается", "Без этого первый звонок — чтение чужой таблицы."),
            ("listen", 3, "buddy", "task", "Два живых звонка наставника", "Новичок только слушает и записывает вопросы."),
            ("first_call", 7, "buddy", "task", "Первый звонок сам", "Наставник рядом, не «ну попробуй с понедельника»."),
            ("checkin_14", 14, "manager", "checkin", "Разговор на 14-й день", "Понимает ли, чего ждут, знает ли, к кому идти, хочет ли остаться."),
            ("own_clients", 30, "manager", "task", "Десять своих клиентов", "Не только слушает чужие сделки."),
            ("checkin_45", 45, "manager", "checkin", "Разговор на 45-й день", "Повторный пульс, пока человек ещё не собрал вещи."),
            ("plan_60", 60, "manager", "task", "План первого месяца", "Факт против нормы, одной цифрой."),
            ("decision_90", 90, "manager", "decision", "Решение на 90-й день", "Остаётся, ещё месяц с планом или расстаёмся."),
        ],
    },
    "office": {
        "label": "Офис",
        "hint": "Доступы в почту, Битрикс и 1С. Пока их нет, человек просто сидит.",
        "points": [
            ("buddy", 0, "manager", "task", "Назначить наставника", "Кто отвечает на вопросы первую неделю, по имени."),
            ("access", 1, "manager", "task", "Доступы: почта, Битрикс, 1С", "Нет доступа — человек пришёл и ждёт. Это частая причина тихого ухода."),
            ("routes", 3, "buddy", "task", "Кому какие задачи нести", "И чего не обещать с порога."),
            ("first_task", 7, "manager", "task", "Первая задача без построчной проверки", "С проверкой результата, не каждой строки."),
            ("checkin_14", 14, "manager", "checkin", "Разговор на 14-й день", "Понимает ли, чего ждут, знает ли, к кому идти, хочет ли остаться."),
            ("quiet_week", 30, "manager", "task", "Неделя без ежедневного контроля", "Сам закрывает обычные задачи, руководитель смотрит итог."),
            ("checkin_45", 45, "manager", "checkin", "Разговор на 45-й день", "Повторный пульс до конца третьего месяца."),
            ("rework", 60, "manager", "task", "Что приходится переделывать", "Один повтор или уже система."),
            ("decision_90", 90, "manager", "decision", "Решение на 90-й день", "Остаётся, ещё месяц с планом или расстаёмся."),
        ],
    },
}

DECISIONS = {
    "stay": "Остаётся",
    "extend": "Ещё месяц с планом",
    "leave": "Расстаёмся",
}

ANSWERS = {
    "understands": {"yes": "Да", "partly": "Частично", "no": "Нет"},
    "knows_who": {"yes": "Да", "no": "Нет"},
    "wants_stay": {"yes": "Да", "unsure": "Сомневаюсь", "no": "Нет"},
}


@dataclass(frozen=True)
class Checkpoint:
    id: int
    code: str
    day_offset: int
    title: str
    detail: str
    owner: str
    kind: str
    done: bool
    result: str


@dataclass(frozen=True)
class Checkin:
    day_offset: int
    understands: str
    knows_who: str
    wants_stay: str
    note: str
    resolved: bool
    resolved_note: str


@dataclass(frozen=True)
class Signal:
    tone: str  # risk | decision | today
    text: str


def role_label(role: str) -> str:
    return ROLES.get(role, {}).get("label", role)


def day_number(today: date, start: date) -> int:
    return (today - start).days


def day_label(n: int) -> str:
    if n <= 0:
        return "вышел сегодня"
    if n > 90:
        return f"{n}-й день, девяносто уже прошли"
    return f"{n}-й день из 90"


def on_board(today: date, start: date) -> bool:
    return 0 <= (today - start).days <= 100


def due_date(start: date, day_offset: int) -> date:
    return start + timedelta(days=day_offset)


def negative_parts(checkin: Checkin) -> list[str]:
    parts: list[str] = []
    if checkin.understands == "no":
        parts.append("не понимает, чего от него ждут")
    elif checkin.understands == "partly":
        parts.append("ожидания понятны только частично")
    if checkin.knows_who == "no":
        parts.append("не знает, к кому идти")
    if checkin.wants_stay == "no":
        parts.append("не хочет оставаться")
    elif checkin.wants_stay == "unsure":
        parts.append("сомневается, оставаться ли")
    return parts


def collect_signals(
    today: date,
    start: date,
    checkpoints: list[Checkpoint],
    checkins: list[Checkin],
) -> list[Signal]:
    """Сигналы, которые руководитель должен разобрать.

    Просроченная точка и тревожный ответ чек-ина — risk.
    Наступивший 90-й день без решения — decision.
    Точка со сроком сегодня — today, это ещё не просрочка.
    """
    by_day = {item.day_offset: item for item in checkins}
    signals: list[Signal] = []
    for point in checkpoints:
        due = due_date(start, point.day_offset)
        if point.kind == "checkin":
            checkin = by_day.get(point.day_offset)
            if checkin is None and due <= today:
                when = "сегодня" if due == today else "просрочен"
                signals.append(Signal("risk", f"Разговор на {point.day_offset}-й день {when}"))
            elif checkin is not None and not checkin.resolved:
                parts = negative_parts(checkin)
                if parts:
                    signals.append(
                        Signal("risk", f"Разговор на {point.day_offset}-й день: " + ", ".join(parts))
                    )
            continue
        if point.done:
            continue
        if point.kind == "decision" and due <= today:
            when = "сегодня" if due == today else "уже пора"
            signals.append(Signal("decision", f"Решение на 90-й день: {when}"))
            continue
        if point.kind != "task":
            continue
        if due < today:
            signals.append(Signal("risk", f"Просрочено: {point.title}"))
        elif due == today:
            signals.append(Signal("today", f"Сегодня: {point.title}"))
    rank = {"risk": 0, "decision": 1, "today": 2}
    signals.sort(key=lambda item: rank[item.tone])
    return signals


def bucket(signals: list[Signal]) -> str:
    if any(item.tone == "risk" for item in signals):
        return "act"
    if any(item.tone == "decision" for item in signals):
        return "act"
    if any(item.tone == "today" for item in signals):
        return "today"
    return "ok"


def point_state(today: date, start: date, point: Checkpoint, checkin: Checkin | None) -> str:
    due = due_date(start, point.day_offset)
    if point.kind == "checkin":
        if checkin is None and due <= today:
            return "risk"
        if checkin is not None and negative_parts(checkin) and not checkin.resolved:
            return "risk"
        if checkin is not None:
            return "done"
    if point.done:
        return "done"
    if point.kind == "decision" and due <= today:
        return "decision"
    if due < today:
        return "risk"
    if due == today:
        return "today"
    return "upcoming"
