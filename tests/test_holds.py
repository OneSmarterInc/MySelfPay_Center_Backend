import unittest
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from center_pro.holds import HoldStatus, PaymentHold


UTC = timezone.utc


class PaymentHoldTests(unittest.TestCase):
    def setUp(self):
        self.started = datetime(2026, 11, 23, 10, 0, tzinfo=UTC)

    def test_uses_seventy_two_hours_when_appointment_is_later(self):
        appointment = self.started + timedelta(days=5)
        hold = PaymentHold.start(self.started, appointment, appointment - timedelta(hours=2))
        self.assertEqual(hold.expires_at, self.started + timedelta(hours=72))

    def test_uses_earlier_appointment_cutoff(self):
        appointment = self.started + timedelta(hours=24)
        cutoff = appointment - timedelta(hours=2)
        hold = PaymentHold.start(self.started, appointment, cutoff)
        self.assertEqual(hold.expires_at, cutoff)

    def test_expires_only_at_deadline_and_never_expires_confirmed_hold(self):
        appointment = self.started + timedelta(days=5)
        hold = PaymentHold.start(self.started, appointment, appointment)
        self.assertEqual(hold.expire(hold.expires_at - timedelta(seconds=1)).status, HoldStatus.PENDING)
        self.assertEqual(hold.expire(hold.expires_at).status, HoldStatus.EXPIRED)
        confirmed = hold.confirm(self.started + timedelta(hours=1))
        self.assertEqual(confirmed.expire(hold.expires_at).status, HoldStatus.CONFIRMED)

    def test_confirmation_at_or_after_deadline_is_rejected(self):
        appointment = self.started + timedelta(days=5)
        hold = PaymentHold.start(self.started, appointment, appointment)
        with self.assertRaisesRegex(ValueError, "no longer payable"):
            hold.confirm(hold.expires_at)
        with self.assertRaisesRegex(ValueError, "no longer payable"):
            hold.expire(hold.expires_at).confirm(hold.expires_at)

    def test_rejects_invalid_or_naive_times(self):
        appointment = self.started + timedelta(days=5)
        with self.assertRaisesRegex(ValueError, "timezone"):
            PaymentHold.start(self.started.replace(tzinfo=None), appointment, appointment)
        with self.assertRaisesRegex(ValueError, "after payment starts"):
            PaymentHold.start(self.started, appointment, self.started)
        with self.assertRaisesRegex(ValueError, "after the appointment"):
            PaymentHold.start(self.started, appointment, appointment + timedelta(seconds=1))

    def test_seventy_two_hours_is_elapsed_time_across_daylight_saving(self):
        eastern = ZoneInfo("America/New_York")
        started = datetime(2026, 3, 7, 10, 0, tzinfo=eastern)
        appointment = datetime(2026, 3, 14, 10, 0, tzinfo=eastern)
        hold = PaymentHold.start(started, appointment, appointment)
        self.assertEqual(hold.expires_at - hold.payment_started_at, timedelta(hours=72))
        self.assertEqual(hold.expires_at, datetime(2026, 3, 10, 15, 0, tzinfo=UTC))


if __name__ == "__main__":
    unittest.main()
