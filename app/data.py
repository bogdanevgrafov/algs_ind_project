from pathlib import Path

import pandas as pd

from app.hashmap import MyHashMap
from app.segtree import SegmentTree

REQUIRED_COLUMNS = [
    "trip_id",
    "trip_start_timestamp",
    "trip_seconds",
    "trip_miles",
    "fare",
    "payment_type",
    "company",
    "pickup_community_area",
    "dropoff_community_area",
]


class TripStore:
    def __init__(self):
        """Метод для инициализации хранилища поездок и основного индекса данных.

        """
        self.root = Path(__file__).resolve().parents[1]
        self.data_dir = self.root / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.data_path = self._resolve_data_path()
        self.df = self._load_data()
        self.trip_index = self._build_trip_index()
        self.slot_start, self.slot_end, self.segment_tree = self._build_segment_tree()

    def _resolve_data_path(self):
        """Метод для выбора локального CSV файла из папки data.


        Returns:
            Path: Путь к CSV-файлу с нужными колонками.
        """
        preferred_names = [
            "chicago_taxi_2024_200k.csv",
        ]
        for name in preferred_names:
            path = self.data_dir / name
            if path.exists():
                try:
                    sample = pd.read_csv(path, nrows=5)
                    missing = [column for column in REQUIRED_COLUMNS if column not in sample.columns]
                    if not missing:
                        return path
                except Exception:
                    continue

        csv_files = sorted(self.data_dir.glob("*.csv"))
        for path in csv_files:
            try:
                sample = pd.read_csv(path, nrows=5)
                missing = [column for column in REQUIRED_COLUMNS if column not in sample.columns]
                if not missing:
                    return path
            except Exception:
                continue

        raise FileNotFoundError(
            "Локальный CSV не найден. Поместите файл в data/ с колонками: "
            + ", ".join(REQUIRED_COLUMNS)
        )

    def _load_data(self):
        """Метод для загрузки локального CSV и подготовки DataFrame.


        Returns:
            pandas.DataFrame: Подготовленный набор данных.
        """
        if not self.data_path.exists():
            raise FileNotFoundError(f"Локальный CSV не найден: {self.data_path}")

        df = pd.read_csv(self.data_path, low_memory=False)
        if df.empty:
            raise ValueError(f"Локальный CSV пустой: {self.data_path}")

        missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
        if missing:
            raise ValueError(f"CSV does not contain required columns: {missing}")

        df = df.loc[:, REQUIRED_COLUMNS].copy()
        df["trip_id"] = df["trip_id"].astype(str)
        df["trip_start_timestamp"] = pd.to_datetime(df["trip_start_timestamp"], errors="coerce")
        df["trip_seconds"] = pd.to_numeric(df["trip_seconds"], errors="coerce")
        df["trip_miles"] = pd.to_numeric(df["trip_miles"], errors="coerce")
        df["fare"] = pd.to_numeric(df["fare"], errors="coerce")
        df["pickup_community_area"] = pd.to_numeric(df["pickup_community_area"], errors="coerce")
        df["dropoff_community_area"] = pd.to_numeric(df["dropoff_community_area"], errors="coerce")
        return df.dropna(subset=["trip_id"]).copy()

    def _build_trip_index(self):
        """Метод для построения индекса trip_id -> row_id через MyHashMap.


        Returns:
            MyHashMap: Индекс поездок.
        """
        index = MyHashMap()
        for row_id, trip_id in enumerate(self.df["trip_id"].tolist()):
            index.put(str(trip_id), row_id)
        return index

    def _build_segment_tree(self):
        """Метод для построения дерева отрезков по 15-минутным слотам времени.


        Returns:
            tuple: Начало периода, конец периода и объект SegmentTree.
        """
        valid = self.df["trip_start_timestamp"].notna()
        if not valid.any():
            return pd.Timestamp("2025-01-01T00:00:00"), pd.Timestamp("2025-01-01T00:00:00"), SegmentTree([(0, 0, 0)])

        timestamps = self.df.loc[valid, "trip_start_timestamp"]
        start = timestamps.min().floor("15min")
        end = timestamps.max().floor("15min")
        slots = int((end - start).total_seconds() // 900) + 1
        values = [(0, 0, 0) for _ in range(slots)]

        for row in self.df.loc[valid].itertuples(index=False):
            ts = row.trip_start_timestamp.floor("15min")
            slot_index = int((ts - start).total_seconds() // 900)
            if slot_index < 0 or slot_index >= slots:
                continue
            trip_count, total_fare, max_fare = values[slot_index]
            fare_value = row.fare if pd.notna(row.fare) else 0
            values[slot_index] = (
                trip_count + 1,
                total_fare + (fare_value if fare_value > 0 else 0),
                max(max_fare, fare_value),
            )

        tree = SegmentTree(values)
        return start, end, tree

    def get_trip_by_id(self, trip_id):
        """Метод для получения поездки по trip_id через индекс.

        Args:
            trip_id: str | int. Идентификатор поездки.

        Returns:
            dict | None: Словарь с данными поездки или None, если поездка не найдена.
        """
        row_id = self.trip_index.get(str(trip_id))
        if row_id is None:
            return None
        row = self.df.iloc[int(row_id)].to_dict()
        if pd.notna(row["trip_start_timestamp"]):
            row["trip_start_timestamp"] = row["trip_start_timestamp"].isoformat()
        return row

    def get_trip_by_id_linear(self, trip_id):
        """Метод для линейного поиска поездки по trip_id.

        Args:
            trip_id: str | int. Идентификатор поездки.

        Returns:
            dict | None: Словарь с данными поездки или None, если поездка не найдена.
        """
        matches = self.df[self.df["trip_id"].astype(str) == str(trip_id)]
        if matches.empty:
            return None
        row = matches.iloc[0].to_dict()
        if pd.notna(row["trip_start_timestamp"]):
            row["trip_start_timestamp"] = row["trip_start_timestamp"].isoformat()
        return row

    def get_summary(self):
        """Метод для расчёта общей статистики по датасету.


        Returns:
            dict: Карточки с метриками и распределение поездок по часам.
        """
        if self.df.empty:
            return {
                "cards": {
                    "trips": 0,
                    "revenue": 0.0,
                    "avg_fare": 0.0,
                    "avg_miles": 0.0,
                },
                "hours": {"labels": [str(i) for i in range(24)], "values": [0 for _ in range(24)]},
            }

        positive_fares = self.df.loc[self.df["fare"] > 0, "fare"]
        positive_miles = self.df.loc[self.df["trip_miles"] >= 0, "trip_miles"]
        hours = self.df["trip_start_timestamp"].dt.hour.value_counts().sort_index().reindex(range(24), fill_value=0)
        return {
            "cards": {
                "trips": int(len(self.df)),
                "revenue": float(positive_fares.sum()) if not positive_fares.empty else 0.0,
                "avg_fare": float(positive_fares.mean()) if not positive_fares.empty else 0.0,
                "avg_miles": float(positive_miles.mean()) if not positive_miles.empty else 0.0,
            },
            "hours": {
                "labels": [str(index) for index in range(24)],
                "values": [int(value) for value in hours.tolist()],
            },
        }

    def _parse_datetime(self, value):
        """Метод для преобразования строки времени в pandas.Timestamp.

        Args:
            value: str. Строковое значение даты и времени.

        Returns:
            pandas.Timestamp: Приведённое время.
        """
        if value is None:
            raise ValueError("Параметр времени не передан")
        try:
            return pd.Timestamp(value)
        except Exception as exc:  # pragma: no cover - simple validation
            raise ValueError(f"Некорректное значение времени: {value}") from exc

    def get_range_stats(self, from_value, to_value):
        """Метод для расчёта статистики по периоду через SegmentTree.

        Args:
            from_value: str. Начало периода.
            to_value: str. Конец периода.

        Returns:
            dict: Количество поездок, выручка и максимум тарифа за период.
        """
        start = self._parse_datetime(from_value).floor("15min")
        end = self._parse_datetime(to_value).floor("15min")
        if start > end:
            raise ValueError("Значение 'from' должно быть меньше или равно 'to'")

        start_index = int((start - self.slot_start).total_seconds() // 900)
        end_index = int((end - self.slot_start).total_seconds() // 900)

        if start_index < 0:
            start_index = 0
        if end_index >= self.segment_tree.n:
            end_index = self.segment_tree.n - 1
        if start_index > end_index:
            return {"count": 0, "revenue": 0.0, "max_fare": 0.0}

        count, revenue, max_fare = self.segment_tree.query(start_index, end_index)
        return {
            "count": int(count),
            "revenue": float(revenue),
            "max_fare": float(max_fare),
        }

    def get_range_stats_naive(self, from_value, to_value):
        """Метод для наивного расчёта статистики по периоду через pandas.

        Args:
            from_value: str. Начало периода.
            to_value: str. Конец периода.

        Returns:
            dict: Количество поездок, выручка и максимум тарифа за период.
        """
        start = self._parse_datetime(from_value)
        end = self._parse_datetime(to_value)
        if start > end:
            raise ValueError("Значение 'from' должно быть меньше или равно 'to'")

        mask = (self.df["trip_start_timestamp"] >= start) & (self.df["trip_start_timestamp"] <= end)
        valid_fares = self.df.loc[mask & (self.df["fare"] > 0), "fare"]
        return {
            "count": int(mask.sum()),
            "revenue": float(valid_fares.sum()) if not valid_fares.empty else 0.0,
            "max_fare": float(self.df.loc[mask, "fare"].max()) if mask.any() else 0.0,
        }
