import os
import asyncio
import random
import time
import argparse
from typing import Dict, Any, List, Tuple

import aiohttp
from dotenv import load_dotenv
from loguru import logger


CATEGORIES = [
    "🪪 Визитки",
    "🖼 Плакаты",
    "📄 Флаеры",
    "🏷️ Наклейки",
    "🖨 Баннеры",
    "🗂 Печать на офисной",
    "🛠️ Индивидуальный заказ",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load test for Telegram bot via sendMessage")
    parser.add_argument("--users", type=int, default=100, help="Number of simulated users")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between user steps (seconds)")
    return parser.parse_args()


def build_api_url(token: str, method: str) -> str:
    return f"https://api.telegram.org/bot{token}/{method}"


async def tg_send_message(session: aiohttp.ClientSession, token: str, chat_id: int, text: str) -> Tuple[bool, float]:
    url = build_api_url(token, "sendMessage")
    payload = {"chat_id": chat_id, "text": text}
    t0 = time.perf_counter()
    try:
        async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            ok = resp.status == 200
            # read body to avoid unclosed connector warnings
            try:
                await resp.text()
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"sendMessage failed for chat_id={chat_id}: {e}")
        ok = False
    dt = time.perf_counter() - t0
    return ok, dt


async def simulate_user(index: int, token: str, delay: float) -> Dict[str, Any]:
    # Each user gets a unique chat_id; use a large random space to avoid collisions
    chat_id = random.randint(10_000_000, 9_999_999_999)
    category = random.choice(CATEGORIES)
    steps_ok: List[bool] = []
    latencies: List[float] = []
    t0 = time.perf_counter()

    async with aiohttp.ClientSession() as http:
        # 1) /start
        ok, dt = await tg_send_message(http, token, chat_id, "/start")
        steps_ok.append(ok); latencies.append(dt)
        await asyncio.sleep(delay)

        # 2) "🧾 Новый заказ"
        ok, dt = await tg_send_message(http, token, chat_id, "🧾 Новый заказ")
        steps_ok.append(ok); latencies.append(dt)
        await asyncio.sleep(delay)

        # 3) Выбор категории
        ok, dt = await tg_send_message(http, token, chat_id, category)
        steps_ok.append(ok); latencies.append(dt)
        await asyncio.sleep(delay)

        # 4) Несколько шагов сценария в зависимости от категории (простейшая имитация)
        # Тираж / количество
        qty = random.choice([50, 100, 150, 200, 3, 5, 10])
        ok, dt = await tg_send_message(http, token, chat_id, str(qty))
        steps_ok.append(ok); latencies.append(dt)
        await asyncio.sleep(delay)

        # Формат или следующий шаг
        fmt = random.choice(["A4", "A3", "A2", "A1", "A0", "90×50 мм", "Односторонние", "Двусторонние"])
        ok, dt = await tg_send_message(http, token, chat_id, fmt)
        steps_ok.append(ok); latencies.append(dt)
        await asyncio.sleep(delay)

        # Файлы — бот принимает документы/фото; симулируем текст-триггер, чтобы пройти дальше
        ok, dt = await tg_send_message(http, token, chat_id, "➡️ Далее")
        steps_ok.append(ok); latencies.append(dt)
        await asyncio.sleep(delay)

        # Телефон (простейший валидный)
        ok, dt = await tg_send_message(http, token, chat_id, "+7 999 123-45-67")
        steps_ok.append(ok); latencies.append(dt)
        await asyncio.sleep(delay)

        # Пожелания (можно пропустить)
        ok, dt = await tg_send_message(http, token, chat_id, "⏭️ Пропустить")
        steps_ok.append(ok); latencies.append(dt)
        await asyncio.sleep(delay)

        # Подтверждение
        ok, dt = await tg_send_message(http, token, chat_id, "✅ Подтвердить")
        steps_ok.append(ok); latencies.append(dt)

    total_time = time.perf_counter() - t0
    success = all(steps_ok)
    return {
        "chat_id": chat_id,
        "category": category,
        "success": success,
        "time": total_time,
        "avg_latency": sum(latencies) / len(latencies) if latencies else 0.0,
    }


async def main_async(users: int, delay: float) -> None:
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        logger.error("BOT_TOKEN is missing in .env")
        return

    logger.info(f"Starting load test: users={users}, delay={delay}s")
    tasks = [simulate_user(i, token, delay) for i in range(users)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    ok = 0
    fail = 0
    times: List[float] = []
    lat_avg: List[float] = []

    for r in results:
        if isinstance(r, Exception):
            logger.error(f"User task failed: {r}")
            fail += 1
            continue
        if r.get("success"):
            ok += 1
        else:
            fail += 1
        times.append(r.get("time", 0.0))
        lat_avg.append(r.get("avg_latency", 0.0))
        logger.opt(colors=True).info(
            f"<green>[chat:{r['chat_id']}]</green> cat='{r['category']}' success={r['success']} time={r['time']:.2f}s avg_lat={r['avg_latency']:.2f}s"
        )

    mean_time = (sum(times) / len(times)) if times else 0.0
    mean_lat = (sum(lat_avg) / len(lat_avg)) if lat_avg else 0.0
    print()
    logger.opt(colors=True).info(f"<green>✅ Успешных заказов: {ok}</green>")
    logger.opt(colors=True).info(f"<yellow>⚠️ Ошибок: {fail}</yellow>")
    logger.opt(colors=True).info(f"<cyan>⏱ Среднее время отклика: {mean_lat:.2f} сек</cyan>")
    logger.opt(colors=True).info(f"<cyan>⏱ Среднее время сценария: {mean_time:.2f} сек</cyan>")


def main() -> None:
    args = parse_args()
    try:
        asyncio.run(main_async(args.users, args.delay))
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")


if __name__ == "__main__":
    main()



