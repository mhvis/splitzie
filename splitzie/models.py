from __future__ import annotations

import decimal
import os.path
import uuid
from secrets import token_urlsafe
from typing import Iterable

from django.contrib.auth.models import AbstractBaseUser, AbstractUser
from django.db import models, transaction
from django.db.models.functions import Lower
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _


class Group(models.Model):
    name = models.CharField(_("name"), max_length=150, default="Group")
    code = models.CharField(max_length=150, default=token_urlsafe, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return reverse("group", kwargs={"code": self.code})

    def __str__(self):
        return self.name


class LinkedEmail(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="emails")
    email = models.EmailField()

    class Meta:
        constraints = [
            models.UniqueConstraint("group", Lower("email"), name="unique_email")
        ]

    def __str__(self):
        return self.email


class Participant(models.Model):
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="participants"
    )
    name = models.CharField(max_length=150)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name

    @cached_property
    def balance(self):
        return Entry.objects.filter(participant=self).balance()


class Payment(models.Model):
    group = models.ForeignKey(Group, on_delete=models.PROTECT, related_name="payments")
    created_at = models.DateTimeField(auto_now_add=True)

    type = models.CharField(
        max_length=10,
        choices=[
            ("expense", "Expense or income"),
            ("settle", "Settlement between participants"),
        ],
    )

    class Meta:
        ordering = ("-created_at",)

    def save_with_entries(self, entries: Iterable[Entry]):
        """Cleans the entries and atomically saves this payment with entries."""
        # Filter null entries
        entries = [e for e in entries if e.amount != 0]

        # There should be at least 1 entry
        if not entries:
            raise ValueError("No entries given")

        # Sanity check: entries must sum to 0
        if sum(e.amount for e in entries) != 0:
            raise ValueError("Sum of entries is not 0!")

        with transaction.atomic():
            self.save()
            for e in entries:
                e.save()

    def get_transfer(self) -> tuple[Participant, Participant, decimal.Decimal]:
        """Get transfer details.

        If this payment contains exactly 2 entries, it's a money transfer
        with a source and target. This method returns the source participant,
        target participant and amount.
        """
        entries = list(self.entries.all())
        if len(entries) != 2:
            raise ValueError("This payment does not strictly contain 2 entries")
        if entries[0].amount > 0:
            # Note: the entry with positive amount is the source in the opposing 'real world' transaction
            return entries[0].participant, entries[1].participant, entries[0].amount
        else:
            return entries[1].participant, entries[0].participant, entries[1].amount


def expense_image_path(instance, filename):
    """Generates a random file path."""
    return "expense/" + str(uuid.uuid4()) + os.path.splitext(filename)[1]


class Expense(Payment):
    # Negative for expenses. Positive for income.
    #
    # An amount of 0 is allowed. This allows for setting a starting balance.
    # We'll show it as income of 0 euros.
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    payer = models.ForeignKey(
        Participant,
        on_delete=models.PROTECT,
        related_name="expenses",
    )
    description = models.CharField(max_length=150)
    image = models.ImageField(upload_to=expense_image_path, blank=True)

    def abs_amount(self):
        return abs(self.amount)

    def is_expense(self):
        return self.amount < 0

    def get_absolute_url(self):
        return reverse("expense", kwargs={"code": self.group.code, "pk": self.pk})


class EntryQuerySet(models.QuerySet):
    def balance(self):
        return self.aggregate(models.Sum("amount", default=decimal.Decimal("0.00")))[
            "amount__sum"
        ].quantize(
            decimal.Decimal("1.00"), context=decimal.Context(traps=[decimal.Inexact])
        )
        # return (
        #     self.aggregate(balance=models.Sum("amount"))["balance"]
        #     or decimal.Decimal("0.00")
        # ).quantize(
        #     decimal.Decimal(10) ** -2, context=decimal.Context(traps=[decimal.Inexact])
        # )


class Entry(models.Model):
    """Each payment modifies the balance of two or more group participants."""

    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name="entries"
    )
    participant = models.ForeignKey(
        Participant, on_delete=models.PROTECT, related_name="entries"
    )
    amount = models.DecimalField(max_digits=7, decimal_places=2)

    objects = EntryQuerySet.as_manager()

    class Meta:
        verbose_name_plural = "entries"
