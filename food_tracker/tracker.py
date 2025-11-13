"""High level API for the food tracking app."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, Iterable, List, Optional

from .ai import FoodRecognitionEngine, RecognisedFood
from .models import DailyLog, FoodEntry, FoodItem, group_entries_by_day
from .storage import FoodLogRepository


@dataclass
class FoodTracker:
    """Coordinates food recognition, logging, and reporting."""

    recogniser: FoodRecognitionEngine
    repository: FoodLogRepository = field(default_factory=FoodLogRepository)
    _entries: List[FoodEntry] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self._entries:
            self._entries.extend(self.repository.load_entries())

    # --- Recognition -----------------------------------------------------
    def scan_description(self, description: str, top_k: int = 3) -> List[RecognisedFood]:
        return self.recogniser.recognise(description, top_k=top_k)

    def register_custom_food(
        self,
        name: str,
        serving_size: str,
        calories: float,
        macronutrients: Optional[Dict[str, float]] = None,
        aliases: Optional[Iterable[str]] = None,
    ) -> FoodItem:
        item = FoodItem(
            name=name,
            serving_size=serving_size,
            calories=calories,
            macronutrients=macronutrients or {},
            aliases=list(aliases or []),
        )
        self.recogniser.add_custom_item(item)
        return item

    # --- Logging ---------------------------------------------------------
    def log_food(self, food_item: FoodItem, quantity: float = 1.0, timestamp: datetime | None = None) -> FoodEntry:
        if timestamp is None:
            timestamp = datetime.utcnow()
        entry = FoodEntry(food=food_item, quantity=quantity, timestamp=timestamp)
        self._entries.append(entry)
        self.repository.save_entries(self._entries)
        return entry

    def manual_food_entry(
        self,
        name: str,
        serving_size: str,
        calories: float,
        quantity: float = 1.0,
        macronutrients: Optional[Dict[str, float]] = None,
    ) -> FoodEntry:
        item = FoodItem(
            name=name,
            serving_size=serving_size,
            calories=calories,
            macronutrients=macronutrients or {},
        )
        return self.log_food(item, quantity=quantity)

    # --- Reporting -------------------------------------------------------
    def entries(self) -> List[FoodEntry]:
        return list(self._entries)

    def entries_for_day(self, target_day: date) -> DailyLog:
        grouped = group_entries_by_day(self._entries)
        if target_day not in grouped:
            return DailyLog(day=target_day)
        return grouped[target_day]

    def daily_summary(self) -> List[DailyLog]:
        grouped = group_entries_by_day(self._entries)
        return [grouped[day] for day in sorted(grouped)]

    def total_calories(self) -> float:
        return sum(entry.calories for entry in self._entries)

    def total_macros(self) -> Dict[str, float]:
        totals: Dict[str, float] = {}
        for entry in self._entries:
            for nutrient, amount in entry.macronutrients.items():
                totals[nutrient] = totals.get(nutrient, 0.0) + amount
        return totals
