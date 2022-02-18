from abc import ABC, abstractmethod


# Class with abstract methods: https://blog.teclado.com/python-abc-abstract-base-classes/
class asset(ABC):
    @abstractmethod
    def calc_revenue(self, hourly_wholesale_price):
        pass

    @abstractmethod
    # update date for next year
    def increment_year(self):
        pass
