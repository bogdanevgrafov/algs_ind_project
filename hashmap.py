class MyHashMap:
    MAX_LOAD_FACTOR = 0.75

    def __init__(self, capacity=8):
        """Метод для создания пустой хеш-таблицы с заданной вместимостью.

        Args:
            capacity: int. Начальная вместимость таблицы.
        """
        self.capacity = capacity
        self.size = 0
        self.buckets = [[] for _ in range(capacity)]

    def _index(self, key):
        """Метод для вычисления индекса бакета по ключу.

        Args:
            key: Ключ, для которого вычисляется индекс.

        Returns:
            int: Номер бакета в пределах capacity.
        """
        return hash(key) % self.capacity

    def load_factor(self):
        """Метод для расчёта коэффициента заполнения таблицы.


        Returns:
            float: Отношение size к capacity.
        """
        return self.size / self.capacity

    def _resize(self):
        """Метод для увеличения размера таблицы и повторного распределения элементов.

        """
        old_buckets = self.buckets
        self.capacity *= 2
        self.buckets = [[] for _ in range(self.capacity)]

        for bucket in old_buckets:
            for key, value in bucket:
                self.buckets[self._index(key)].append((key, value))

    def put(self, key, value):
        """Метод для добавления или обновления значения по ключу.

        Args:
            key: Ключ записи.
            value: Значение записи.
        """
        bucket = self.buckets[self._index(key)]

        for i, (_key, _value) in enumerate(bucket):
            if _key == key:
                bucket[i] = (key, value)
                return

        if (self.size + 1) / self.capacity > self.MAX_LOAD_FACTOR:
            self._resize()
            bucket = self.buckets[self._index(key)]

        bucket.append((key, value))
        self.size += 1

    def get(self, key):
        """Метод для получения значения по ключу.

        Args:
            key: Ключ, который нужно найти.

        Returns:
            object | None: Значение по ключу или None, если ключ отсутствует.
        """
        index = self._index(key)
        for _key, value in self.buckets[index]:
            if key == _key:
                return value
        return None

    def contains(self, key):
        """Метод для проверки наличия ключа в таблице.

        Args:
            key: object. Ключ, наличие которого проверяется.

        Returns:
            bool: True, если ключ найден, иначе False.
        """
        index = self._index(key)
        for _key, value in self.buckets[index]:
            if key == _key:
                return True
        return False

    def remove(self, key):
        """Метод для удаления записи по ключу.

        Args:
            key: object. Ключ удаляемой записи.

        Returns:
            bool: True, если ключ был удалён, иначе False.
        """
        index = self._index(key)
        bucket = self.buckets[index]
        for i, (_key, _value) in enumerate(bucket):
            if _key == key:
                bucket.pop(i)
                self.size -= 1
                return True
        return False

    def stats(self):
        """Метод для получения статистики по наполнению хеш-таблицы.


        Returns:
            dict: Словарь со статистикой по размеру, capacity, load factor и длинам бакетов.
        """
        lengths = [len(bucket) for bucket in self.buckets]
        return {
            "size": self.size,
            "capacity": self.capacity,
            "load_factor": self.load_factor(),
            "empty_buckets": lengths.count(0),
            "max_bucket_len": max(lengths),
            "longest_bucket": max(lengths),
        }

    def __len__(self):
        """Метод для получения числа элементов в таблице.


        Returns:
            int: Количество сохранённых элементов.
        """
        return self.size
