"""Lightweight AI helpers for recognising food items from free text."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from .models import FoodItem

_TOKEN_RE = re.compile(r"[\w']+")


def _tokenize(text: str) -> List[str]:
    return _TOKEN_RE.findall(text.lower())


def _normalise(vector: Dict[str, float]) -> Dict[str, float]:
    norm = math.sqrt(sum(value * value for value in vector.values())) or 1.0
    return {key: value / norm for key, value in vector.items()}


def _cosine_similarity(a: Dict[str, float], b: Dict[str, float]) -> float:
    common = set(a) & set(b)
    return sum(a[key] * b[key] for key in common)


@dataclass
class RecognisedFood:
    """Return type for a recognition result."""

    item: FoodItem
    confidence: float


class EmbeddingModel:
    """A tiny bag-of-words embedding to keep the project self-contained."""

    def encode(self, texts: Sequence[str]) -> List[Dict[str, float]]:
        embeddings: List[Dict[str, float]] = []
        for text in texts:
            counts = Counter(_tokenize(text))
            embeddings.append(_normalise(counts))
        return embeddings


class FoodRecognitionEngine:
    """Recognise food items from free text descriptions.

    The engine ships with a curated dataset but can be extended at runtime.
    It intentionally uses a lightweight embedding so that it works offline while
    exposing an API that can later be replaced with a heavier AI model.
    """

    def __init__(self, reference_path: Path | None = None) -> None:
        if reference_path is None:
            reference_path = Path(__file__).resolve().parent / "data" / "foods.json"
        if not reference_path.exists():
            raise FileNotFoundError(f"Food reference file not found: {reference_path}")

        self._embedding = EmbeddingModel()
        self._reference_items = self._load_reference(reference_path)
        self._reference_vectors = self._embedding.encode(
            [self._item_representation(item) for item in self._reference_items]
        )

    @staticmethod
    def _item_representation(item: FoodItem) -> str:
        aliases = ", ".join(item.aliases)
        macros = ", ".join(f"{nutrient}:{amount}" for nutrient, amount in item.macronutrients.items())
        return f"{item.name} serving {item.serving_size} {aliases} {macros}"

    def _load_reference(self, path: Path) -> List[FoodItem]:
        with path.open("r", encoding="utf8") as handle:
            data = json.load(handle)
        items = []
        for record in data:
            items.append(
                FoodItem(
                    name=record["name"],
                    serving_size=record.get("serving_size", "1 serving"),
                    calories=float(record.get("calories", 0)),
                    macronutrients=record.get("macronutrients", {}),
                    aliases=record.get("aliases", []),
                )
            )
        return items

    def known_items(self) -> List[FoodItem]:
        return list(self._reference_items)

    def recognise(self, description: str, top_k: int = 3) -> List[RecognisedFood]:
        if not description.strip():
            return []

        description_vector = self._embedding.encode([description])[0]
        scored: List[RecognisedFood] = []
        for item, vector in zip(self._reference_items, self._reference_vectors):
            confidence = _cosine_similarity(description_vector, vector)
            if item.matches(description):
                confidence = max(confidence, 0.99)
            scored.append(RecognisedFood(item=item, confidence=confidence))
        scored.sort(key=lambda result: result.confidence, reverse=True)
        return scored[:top_k]

    def add_custom_item(self, item: FoodItem) -> None:
        self._reference_items.append(item)
        self._reference_vectors.append(
            self._embedding.encode([self._item_representation(item)])[0]
        )

    def scan_bulk(self, descriptions: Iterable[str]) -> List[List[RecognisedFood]]:
        return [self.recognise(description) for description in descriptions]
