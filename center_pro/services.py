from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, PermissionDenied, NotFound
from .models import AuditEvent, BookingRequest, Membership, Slot, Center, WorkingHours

class Conflict(APIException):
    status_code = 409
    default_detail = 'This time is no longer available. Choose another slot.'

@transaction.atomic
def confirm_booking(*, user, center_id, booking_id, slot_id):
    # Lock one center first, serializing conflicting confirmations across its resources.
    try:
        center = Center.objects.select_for_update().get(pk=center_id)
    except Center.DoesNotExist:
        raise NotFound()
    if not Membership.objects.filter(center=center, user=user, role=Membership.Role.STAFF).exists():
        raise PermissionDenied('Staff access is required to confirm appointments.')
    try:
        booking = BookingRequest.objects.select_for_update().get(pk=booking_id, center=center)
        slot = Slot.objects.get(pk=slot_id, center=center)
    except (BookingRequest.DoesNotExist, Slot.DoesNotExist):
        raise NotFound()
    if booking.status == BookingRequest.Status.CONFIRMED:
        if booking.slot_id == slot.id:
            return booking  # Safe retry after a lost response: no duplicate audit event.
        raise Conflict('This appointment is already confirmed. Rescheduling is not implemented yet.')
    from django.utils.dateparse import parse_datetime
    preferred_times=[]
    for value in booking.preferred_windows:
        try:
            at=parse_datetime(value)
            if at and timezone.is_aware(at): preferred_times.append(at)
        except (ValueError, TypeError): pass
    from .preferences import preference_bounds
    from rest_framework.exceptions import ValidationError
    period_match=False
    for preference in booking.preferred_windows:
        if isinstance(preference,dict):
            try:
                begin,end=preference_bounds(center,preference)
                period_match=period_match or (begin<=slot.starts_at and slot.ends_at<=end)
            except ValidationError: pass
    if slot.id not in booking.preferred_slot_ids and slot.starts_at not in preferred_times and not period_match:
        raise Conflict('Select one of the patient-submitted times. New choices are required for legacy requests.')
    if slot.blocked or slot.starts_at <= timezone.now():
        raise Conflict()
    from zoneinfo import ZoneInfo
    start=slot.starts_at.astimezone(ZoneInfo(center.timezone))
    end=slot.ends_at.astimezone(ZoneInfo(center.timezone))
    hours=WorkingHours.objects.filter(center=center,weekday=start.weekday()).first()
    if not hours or hours.closed or start.date()!=end.date() or start.time()<hours.opens or end.time()>hours.closes:
        raise Conflict('This slot is outside the current working hours. Review availability before confirming.')
    overlap = BookingRequest.objects.filter(center=center, status='confirmed', slot__resource__iexact=slot.resource, slot__starts_at__lt=slot.ends_at, slot__ends_at__gt=slot.starts_at)
    if overlap.exists():
        raise Conflict()
    booking.slot = slot
    booking.status = BookingRequest.Status.CONFIRMED
    booking.confirmed_by = user
    booking.confirmed_at = timezone.now()
    booking.save(update_fields=['slot', 'status', 'confirmed_by', 'confirmed_at'])
    AuditEvent.objects.create(center=center, actor=user, action='appointment.confirmed', reference=booking.reference)
    return booking
