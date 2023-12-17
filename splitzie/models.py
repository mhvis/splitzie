from __future__ import annotations

import decimal
import os.path
import uuid
from secrets import token_urlsafe
from typing import Iterable

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, AbstractUser
from django.db import models, transaction
from django.db.models.functions import Lower
from django.urls import reverse
from django.utils import translation
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from splitzie.mail import send_rendered_mail
from splitzie.settle import Settler, SettleEntry


class Group(models.Model):
    name = models.CharField(_("name"), max_length=150, default=_("My group"))
    code = models.CharField(
        _("code"), max_length=150, default=token_urlsafe, unique=True
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("group")
        verbose_name_plural = _("groups")

    def get_absolute_url(self):
        return reverse("group", kwargs={"code": self.code})

    def get_moves(self):
        settler = Settler([SettleEntry(p, p.balance) for p in self.participants.all()])
        moves = settler.get_optimal_brute_force()
        return moves

    def send_mail(
        self, email_template_name: str, subject_template_name: str, context: dict = None
    ):
        """Sends a (separate) email to each linked e-mail address.

        See:
            LinkedEmail.send_mail
        """
        for linked_email in self.emails.all():
            linked_email.send_mail(email_template_name, subject_template_name, context)

    def __str__(self):
        return self.name


class LinkedEmail(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="emails")
    email = models.EmailField(_("e-mail"))
    language = models.CharField(_("language"), max_length=5, choices=settings.LANGUAGES)

    class Meta:
        constraints = [
            models.UniqueConstraint("group", Lower("email"), name="unique_email")
        ]

    def send_mail(
        self, email_template_name: str, subject_template_name: str, context: dict = None
    ):
        """Sends a mail in the correct language."""
        if context is None:
            context = {}

        context["linked_email"] = self
        with translation.override(self.language):
            # It's probably better (for testing) to return a list of e-mails instead of directly sending them
            send_rendered_mail(
                email_template_name, subject_template_name, [self.email], context
            )

    def __str__(self):
        return self.email


class Participant(models.Model):
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="participants"
    )
    name = models.CharField(_("name"), max_length=150)

    class Meta:
        ordering = ("name",)
        verbose_name = _("participant")
        verbose_name_plural = _("participants")

    def __str__(self):
        return self.name

    @cached_property
    def balance(self):
        return Entry.objects.filter(participant=self).balance()


class Payment(models.Model):
    group = models.ForeignKey(Group, on_delete=models.PROTECT, related_name="payments")
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    type = models.CharField(
        max_length=10,
        choices=[
            ("expense", "Expense or income"),
            ("settle", "Settlement between participants"),
        ],
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("payment")
        verbose_name_plural = _("payments")

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

        # Sanity check: participants must be part of the same group
        for entry in entries:
            if entry.participant.group != self.group:
                raise ValueError("Participant is not part of this group")

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
    amount = models.DecimalField(_("amount"), max_digits=7, decimal_places=2)
    payer = models.ForeignKey(
        Participant,
        on_delete=models.PROTECT,
        related_name="expenses",
    )
    description = models.CharField(_("description"), max_length=150)
    image = models.ImageField(upload_to=expense_image_path, blank=True)

    class Meta:
        verbose_name = _("expense")
        verbose_name_plural = _("expenses")

    def abs_amount(self):
        return abs(self.amount)

    def is_expense(self):
        return self.amount < 0

    def get_absolute_url(self):
        return reverse("expense", kwargs={"code": self.group.code, "pk": self.pk})

    def get_division(self) -> list[tuple[Entry, decimal.Decimal]]:
        """Returns the division as how it was entered in the form originally."""
        sign = -1 if self.is_expense() else 1
        return [
            (
                e,
                sign
                * (e.amount if e.participant != self.payer else e.amount + self.amount),
            )
            for e in self.entries.all()
        ]


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
    amount = models.DecimalField(_("amount"), max_digits=7, decimal_places=2)

    objects = EntryQuerySet.as_manager()

    class Meta:
        verbose_name_plural = "entries"
