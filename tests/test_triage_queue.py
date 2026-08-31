import unittest
from datetime import datetime, timedelta, timezone

from triage_queue import Patient, QueueEmptyError, TriageQueue


class PatientValidationTests(unittest.TestCase):
    def test_valid_patient_is_created(self) -> None:
        patient = Patient(name="  Jane Doe  ", triage_level=2)
        self.assertEqual(patient.name, "Jane Doe")
        self.assertEqual(patient.triage_level, 2)
        self.assertIsInstance(patient.arrived_at, datetime)

    def test_empty_name_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            Patient(name="   ", triage_level=1)

    def test_invalid_triage_level_raises_value_error(self) -> None:
        for level in (0, 4, -1, "2"):
            with self.assertRaises(ValueError):
                Patient(name="John", triage_level=level)  # type: ignore[arg-type]


class TriageQueueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.queue = TriageQueue()
        self.base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    def _patient(self, name: str, level: int, seconds: int) -> Patient:
        return Patient(name=name, triage_level=level, arrived_at=self.base + timedelta(seconds=seconds))

    def test_is_empty_and_len(self) -> None:
        self.assertTrue(self.queue.is_empty())
        self.assertEqual(len(self.queue), 0)

        self.queue.enqueue(self._patient("Ana", 3, 0))

        self.assertFalse(self.queue.is_empty())
        self.assertEqual(len(self.queue), 1)

    def test_enqueue_requires_patient_instance(self) -> None:
        with self.assertRaises(TypeError):
            self.queue.enqueue("not-a-patient")  # type: ignore[arg-type]

    def test_dequeue_empty_raises_custom_exception(self) -> None:
        with self.assertRaises(QueueEmptyError):
            self.queue.dequeue()

    def test_peek_empty_returns_none(self) -> None:
        self.assertIsNone(self.queue.peek())

    def test_priority_then_fifo_by_arrival(self) -> None:
        p1 = self._patient("Standard First", 3, 0)
        p2 = self._patient("Critical Later", 1, 10)
        p3 = self._patient("Urgent Middle", 2, 5)
        p4 = self._patient("Critical Earliest", 1, 2)

        self.queue.enqueue(p1)
        self.queue.enqueue(p2)
        self.queue.enqueue(p3)
        self.queue.enqueue(p4)

        ordered = self.queue.list_queue()
        self.assertEqual(
            [patient.name for patient in ordered],
            ["Critical Earliest", "Critical Later", "Urgent Middle", "Standard First"],
        )

        self.assertEqual(self.queue.dequeue().name, "Critical Earliest")
        self.assertEqual(self.queue.dequeue().name, "Critical Later")
        self.assertEqual(self.queue.dequeue().name, "Urgent Middle")
        self.assertEqual(self.queue.dequeue().name, "Standard First")
        self.assertTrue(self.queue.is_empty())

    def test_fifo_when_timestamp_equal(self) -> None:
        timestamp = self.base
        p1 = Patient(name="A", triage_level=2, arrived_at=timestamp)
        p2 = Patient(name="B", triage_level=2, arrived_at=timestamp)
        p3 = Patient(name="C", triage_level=2, arrived_at=timestamp)

        self.queue.enqueue(p1)
        self.queue.enqueue(p2)
        self.queue.enqueue(p3)

        self.assertEqual(self.queue.dequeue().name, "A")
        self.assertEqual(self.queue.dequeue().name, "B")
        self.assertEqual(self.queue.dequeue().name, "C")

    def test_peek_does_not_remove_patient(self) -> None:
        patient = self._patient("Mario", 1, 0)
        self.queue.enqueue(patient)

        peeked = self.queue.peek()
        self.assertIsNotNone(peeked)
        self.assertEqual(peeked.name, "Mario")
        self.assertEqual(len(self.queue), 1)

    def test_stats_counts_by_level(self) -> None:
        self.queue.enqueue(self._patient("P1", 1, 0))
        self.queue.enqueue(self._patient("P2", 1, 1))
        self.queue.enqueue(self._patient("P3", 3, 2))

        self.assertEqual(self.queue.stats(), {1: 2, 2: 0, 3: 1})

        self.queue.dequeue()
        self.assertEqual(self.queue.stats(), {1: 1, 2: 0, 3: 1})


if __name__ == "__main__":
    unittest.main()
