import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.data import TripStore

ROOT = Path(__file__).resolve().parents[1]
app = FastAPI(title="Taxi Trips Explorer")
app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")
store = TripStore()


@app.get("/")
def serve_index():
    """Метод для отдачи главной HTML-страницы проекта.


    Returns:
        FileResponse: HTML-страница интерфейса.
    """
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/summary")
def get_summary():
    """Метод для расчёта общей аналитики по поездкам.


    Returns:
        dict: Карточки с итогами и распределение поездок по часам.
    """
    return store.get_summary()


@app.get("/api/trip/{trip_id}")
def get_trip(trip_id: str):
    """Метод для поиска поездки по trip_id с замером времени хеш-индекса и линейного поиска.

    Args:
        trip_id: str. Идентификатор поездки.

    Returns:
        dict: Данные поездки и время поиска двумя способами.
    """
    start = time.perf_counter()
    trip = store.get_trip_by_id(trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Поездка не найдена")
    hash_time_ms = (time.perf_counter() - start) * 1000.0

    linear_start = time.perf_counter()
    linear_trip = store.get_trip_by_id_linear(trip_id)
    if linear_trip is None:
        raise HTTPException(status_code=404, detail="Поездка не найдена")
    linear_time_ms = (time.perf_counter() - linear_start) * 1000.0

    return {
        "trip": trip,
        "time_ms": {
            "hashmap": round(hash_time_ms, 4),
            "linear": round(linear_time_ms, 4),
        },
    }


@app.get("/api/index-stats")
def get_index_stats():
    """Метод для получения статистики хеш-таблицы.


    Returns:
        dict: Размер, вместимость, load factor и длины бакетов.
    """
    return store.trip_index.stats()


@app.get("/api/range")
def get_range_stats(from_value: str = Query(..., alias="from"), to: str = Query(..., alias="to")):
    """Метод для расчёта статистики периода через SegmentTree и сравнения с наивным вариантом.

    Args:
        from_value: str. Начало периода.
        to: str. Конец периода.

    Returns:
        dict: Результаты дерева и наивного расчёта.
    """
    try:
        start_tree = time.perf_counter()
        tree_stats = store.get_range_stats(from_value, to)
        tree_time_ms = (time.perf_counter() - start_tree) * 1000.0

        start_common = time.perf_counter()
        common_stats = store.get_range_stats_naive(from_value, to)
        common_time_ms = (time.perf_counter() - start_common) * 1000.0
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "from": from_value,
        "to": to,
        "tree": tree_stats,
        "common": common_stats,
        "matches": tree_stats == common_stats,
        "time_ms": {
            "tree": round(tree_time_ms, 4),
            "common": round(common_time_ms, 4),
        },
    }


@app.get("/health")
def health():
    """Метод для проверки статуса сервера.


    Returns:
        dict: Рабочий статус сервиса.
    """
    return {"status": "ok"}
