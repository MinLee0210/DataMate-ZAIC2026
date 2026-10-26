from abc import ABC, abstractmethod


class DataSource(ABC):
    """A backing store (one business's DuckDB file). Services receive one of these."""

    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def ping(self) -> None:
        """Raise if the datasource is unreachable."""
