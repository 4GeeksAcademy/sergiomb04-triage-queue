from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import heapq
from itertools import count
from typing import Optional


TRIAGE_LABELS = {
    1: "Critical",
    2: "Urgent",
    3: "Standard",
}


@dataclass(slots=True)
class Patient:
    name: str
    triage_level: int
    arrived_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Patient name must be a non-empty string.")

        if not isinstance(self.triage_level, int) or self.triage_level not in (1, 2, 3):
            raise ValueError("triage_level must be an integer in {1, 2, 3}.")

        if not isinstance(self.arrived_at, datetime):
            raise ValueError("arrived_at must be a datetime instance.")

        self.name = self.name.strip()


class QueueEmptyError(IndexError):
    """Raised when attempting to extract from an empty queue."""


class TriageQueue:
    def __init__(self) -> None:
        self._heap: list[tuple[int, datetime, int, Patient]] = []
        self._counter = count()
        self._counts = {1: 0, 2: 0, 3: 0}

    def enqueue(self, patient: Patient) -> None:
        if not isinstance(patient, Patient):
            raise TypeError("enqueue expects a Patient instance.")

        heapq.heappush(
            self._heap,
            (patient.triage_level, patient.arrived_at, next(self._counter), patient),
        )
        self._counts[patient.triage_level] += 1

    def dequeue(self) -> Patient:
        if not self._heap:
            raise QueueEmptyError("Cannot dequeue from an empty triage queue.")

        _, _, _, patient = heapq.heappop(self._heap)
        self._counts[patient.triage_level] -= 1
        return patient

    def peek(self) -> Optional[Patient]:
        if not self._heap:
            return None
        return self._heap[0][3]

    def list_queue(self) -> list[Patient]:
        ordered_entries = sorted(self._heap)
        return [entry[3] for entry in ordered_entries]

    def stats(self) -> dict[int, int]:
        return {1: self._counts[1], 2: self._counts[2], 3: self._counts[3]}

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def __len__(self) -> int:
        return len(self._heap)


def _format_patient(patient: Patient) -> str:
    arrived_text = patient.arrived_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    return f"{patient.name} | Level {patient.triage_level} ({TRIAGE_LABELS[patient.triage_level]}) | {arrived_text}"


def _read_non_empty_name() -> str:
    while True:
        name = input("Patient name: ").strip()
        if name:
            return name
        print("Name cannot be empty.")


def _read_triage_level() -> int:
    while True:
        raw = input("Triage level (1=Critical, 2=Urgent, 3=Standard): ").strip()
        try:
            level = int(raw)
        except ValueError:
            print("Please enter a valid integer (1, 2, or 3).")
            continue

        if level not in (1, 2, 3):
            print("Invalid level. Choose 1, 2, or 3.")
            continue

        return level


def _print_menu() -> None:
    print("\n=== Triage Queue Menu ===")
    print("1. Add Patient")
    print("2. Call Next Patient")
    print("3. View Queue")
    print("4. View Stats")
    print("5. Exit")


def run_cli() -> None:
    queue = TriageQueue()

    while True:
        _print_menu()
        choice = input("Choose an option (1-5): ").strip()

        if choice == "1":
            name = _read_non_empty_name()
            level = _read_triage_level()
            patient = Patient(name=name, triage_level=level)
            queue.enqueue(patient)
            print(f"Added: {_format_patient(patient)}")

        elif choice == "2":
            try:
                next_patient = queue.dequeue()
            except QueueEmptyError as exc:
                print(str(exc))
            else:
                print(f"Next patient: {_format_patient(next_patient)}")

        elif choice == "3":
            waiting = queue.list_queue()
            if not waiting:
                print("Queue is empty.")
            else:
                print("\nDispatch order:")
                for index, patient in enumerate(waiting, start=1):
                    print(f"{index}. {_format_patient(patient)}")

        elif choice == "4":
            counts = queue.stats()
            total = len(queue)
            print("\nQueue stats:")
            print(f"Level 1 (Critical): {counts[1]}")
            print(f"Level 2 (Urgent): {counts[2]}")
            print(f"Level 3 (Standard): {counts[3]}")
            print(f"Total waiting: {total}")

        elif choice == "5":
            print("Exiting triage queue manager.")
            break

        else:
            print("Invalid option. Choose a number from 1 to 5.")


if __name__ == "__main__":
    run_cli()
