class SegmentTree:
    def __init__(self, a):
        """Метод для создания дерева отрезков на основе массива.

        Args:
            a: list. Исходный массив значений для построения дерева.
        """
        self.n = len(a)
        self.a = list(a)
        self.tree = [0] * (4 * max(self.n, 1))
        if self.n > 0:
            self._build(1, 0, self.n - 1)

    def _combine(self, left, right):
        """Метод для объединения значений левого и правого узлов.

        Args:
            left: int | tuple. Значение левого дочернего узла.
            right: int | tuple. Значение правого дочернего узла.

        Returns:
            int | tuple: Комбинированное значение для родительского узла.
        """
        if isinstance(left, tuple) and isinstance(right, tuple):
            if len(left) == 3 and len(right) == 3:
                return (
                    left[0] + right[0],
                    left[1] + right[1],
                    max(left[2], right[2]),
                )
            return tuple(x + y for x, y in zip(left, right))
        return left + right

    def _build(self, v, tl, tr):
        """Метод для рекурсивного построения дерева отрезков.

        Args:
            v: int. Номер вершины в массиве дерева.
            tl: int. Левая граница текущего сегмента.
            tr: int. Правая граница текущего сегмента.
        """
        if tl == tr:
            self.tree[v] = self.a[tl]
            return
        tm = (tl + tr) // 2
        self._build(2 * v, tl, tm)
        self._build(2 * v + 1, tm + 1, tr)
        self.tree[v] = self._combine(self.tree[2 * v], self.tree[2 * v + 1])

    def query(self, l, r):
        """Метод для запроса суммы или агрегата в диапазоне [l, r].

        Args:
            l: int. Левая граница диапазона.
            r: int. Правая граница диапазона.

        Returns:
            int | tuple: Результат по диапазону.
        """
        if self.n == 0:
            raise ValueError("Массив пустой")
        if not (0 <= l <= r < self.n):
            raise ValueError(f"Неверные границы: {l}, {r}")
        return self._query(1, 0, self.n - 1, l, r)

    def _query(self, v, tl, tr, l, r):
        """Метод для рекурсивного поиска по диапазону.

        Args:
            v: int. Номер вершины текущего сегмента.
            tl: int. Левая граница текущего сегмента.
            tr: int. Правая граница текущего сегмента.
            l: int. Левая граница поиска.
            r: int. Правая граница поиска.

        Returns:
            int | tuple: Значение среза дерева для заданного диапазона.
        """
        if r < tl or tr < l:
            if isinstance(self.a[0], tuple) and len(self.a[0]) == 3:
                return (0, 0, 0)
            return 0
        if l <= tl and tr <= r:
            return self.tree[v]
        tm = (tl + tr) // 2
        left_res = self._query(2 * v, tl, tm, l, r)
        right_res = self._query(2 * v + 1, tm + 1, tr, l, r)
        return self._combine(left_res, right_res)

    def update(self, pos, value):
        """Метод для обновления значения в позиции pos.

        Args:
            pos: int. Индекс элемента, который надо обновить.
            value: int | tuple. Новое значение элемента.
        """
        if not (0 <= pos < self.n):
            raise ValueError(f"Неверная позиция: {pos}")
        self.a[pos] = value
        self._update(1, 0, self.n - 1, pos, value)

    def _update(self, v, tl, tr, pos, value):
        """Метод для рекурсивного обновления дерева после изменения элемента.

        Args:
            v: int. Номер вершины текущего сегмента.
            tl: int. Левая граница текущего сегмента.
            tr: int. Правая граница текущего сегмента.
            pos: int. Индекс обновляемого элемента.
            value: int | tuple. Новое значение элемента.
        """
        if tl == tr:
            self.tree[v] = value
            return
        tm = (tl + tr) // 2
        if pos <= tm:
            self._update(2 * v, tl, tm, pos, value)
        else:
            self._update(2 * v + 1, tm + 1, tr, pos, value)
        self.tree[v] = self._combine(self.tree[2 * v], self.tree[2 * v + 1])

    def point_update(self, index, value):
        """Метод для обновления элемента по индексу, alias для update.

        Args:
            index: int. Индекс элемента.
            value: int | tuple. Новое значение элемента.
        """
        self.update(index, value)

    def build_from_values(self, values):
        """Метод для постройки дерева заново по новому массиву значений.

        Args:
            values: list. Новый массив значений.
        """
        self.a = list(values)
        self.n = len(self.a)
        self.tree = [0] * (4 * max(self.n, 1))
        if self.n > 0:
            self._build(1, 0, self.n - 1)
