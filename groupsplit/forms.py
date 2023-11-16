# from django import forms
# from django.contrib.auth.forms import BaseUserCreationForm, ReadOnlyPasswordHashField
# from django.core.exceptions import ValidationError
# from django.forms import inlineformset_factory
# from django.utils.translation import gettext_lazy as _
#
# from groupsplit.models import Entry
#
#
#
# class BaseEntryFormSet(forms.BaseInlineFormSet):
#     def __init__(self, *args, **kwargs):
#         if "initial" in kwargs:
#             self.extra = len(kwargs["initial"])
#         super().__init__(*args, **kwargs)
#
#     def clean(self):
#         super().clean()
#         if any(self.errors):
#             return
#         amounts = [a for a in (f.cleaned_data.get("amount") for f in self.forms) if a]
#         if not amounts:
#             raise ValidationError("No amounts given.")
#         if sum(amounts) != 0:
#             raise ValidationError("Amounts do not sum to zero.")
#
#
# EntryFormSet = inlineformset_factory(
#     Transaction,
#     Entry,
#     # form=EntryForm,
#     formset=BaseEntryFormSet,
#     fields=["user", "amount"],
#     # can_delete=False,
#     # edit_only=False,
#     # extra=2,
#     # max_num=1000
#     # extra=0,
#     # extra=100,
#     # max_num=1,
#     # extra=len(list(user_set)),
#     can_order=False,
#     can_delete=False,
#     # extra=0,
#     # validate_min=True,
#     # min_num=2,
# )
#
#
#
# class TransactionExpenseForm(forms.ModelForm):
#     direction = forms.ChoiceField(
#         choices=(("expense", "Expense"), ("income", "Income")),
#         label="Type",
#         widget=forms.RadioSelect(),
#         initial="expense",
#     )
#     expense_amount = forms.DecimalField(
#         max_digits=7, decimal_places=2, min_value=0, label="Amount"
#     )
#     expense_user = forms.ModelChoiceField(User.objects.all(), empty_label=None, label="Payee")
#
#     class Meta:
#         model = Transaction
#         fields = ("description", "expense_user", "expense_amount")
#
#     def __init__(self, *args, initial=None, instance=None, **kwargs):
#         initial = initial or {}
#         initial.update({"expense_user": instance.created_by})
#         super().__init__(*args, initial=initial, instance=instance, **kwargs)
#         users = self.instance.group.user_set.all()
#         # self.fields["expense_user"].initial = str(self.instance.created_by.pk)
#         self.fields["expense_user"].queryset = users
#         # self.fields["expense_amount"].field.min_value = 0
#
#         # Add fields for the entries
#         for user in users:
#             self.fields[f"entry_{user.pk}"] = forms.DecimalField(
#                 max_digits=7,
#                 decimal_places=2,
#                 required=False,
#                 label=user.get_full_name(),
#             )
#
#     def entry_fields(self):
#         """Returns all fields for entry amounts."""
#         return (field for field in self if field.name.startswith("entry_"))
#
#     def non_entry_fields(self):
#         return (field for field in self if not field.name.startswith("entry_"))
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from groupsplit.models import Expense, Participant, Entry, Payment


class ExpenseForm(forms.ModelForm):
    type = forms.ChoiceField(choices=[("expense", "Expense"), ("income", "Income")])
    amount = forms.DecimalField(
        max_digits=7, decimal_places=2, min_value=Decimal("0.01")
    )

    class Meta:
        model = Expense
        fields = ["amount", "payer", "description", "image"]

    def __init__(self, *args, instance=None, **kwargs):
        super().__init__(*args, instance=instance, **kwargs)
        self.participants = Participant.objects.filter(group=instance.group)

        # Fields for each participant
        for participant in self.participants:
            self.fields[f"participant-{participant.pk}"] = forms.DecimalField(
                max_digits=7, decimal_places=2, required=False
            )

        # Payer must be participant
        self.fields["payer"].queryset = self.participants

    def clean(self):
        cleaned_data = super().clean()

        # Sum of division must be equal to total amount
        division_sum = sum(
            cleaned_data.get(f"participant-{p.pk}", 0) for p in self.participants
        )
        if division_sum != cleaned_data.get("amount", 0):
            raise ValidationError("Division values do not sum up to the total amount.")

        # Amount must be corrected for expense/income
        if cleaned_data.get("type") == "expense":
            cleaned_data["amount"] = -1 * cleaned_data.get("amount", Decimal("0.00"))

        return cleaned_data

    def save(self, commit=True):
        obj = super().save(commit=False)  # type: Expense

        if not commit:
            return obj

        def get_amount(p: Participant):
            """Entry amount depends on type and whether the participant is payer/receiver."""
            amount = self.cleaned_data.get(f"participant-{p.pk}", 0)

            # Flip sign when expense
            if self.cleaned_data["type"] == "expense":
                amount *= -1

            if p == obj.payer:
                amount -= obj.amount

            return amount

        obj.save_with_entries(
            Entry(
                payment=obj,
                participant=p,
                amount=get_amount(p),
            )
            for p in self.participants
        )

        return obj


class SettleForm(forms.ModelForm):
    debtor = forms.ModelChoiceField(queryset=Participant.objects.none())
    creditor = forms.ModelChoiceField(queryset=Participant.objects.none())
    amount = forms.DecimalField(
        max_digits=7, decimal_places=2, min_value=Decimal("0.01")
    )

    class Meta:
        model = Payment
        fields = []

    def __init__(self, *args, instance=None, **kwargs):
        super().__init__(*args, instance=instance, **kwargs)
        # Debtor/creditor must be part of the group
        self.fields["debtor"].queryset = instance.group.participants.all()
        self.fields["creditor"].queryset = instance.group.participants.all()

    def clean(self):
        cleaned_data = super().clean()
        debtor = cleaned_data.get("debtor")  # type: Participant
        creditor = cleaned_data.get("creditor")  # type: Participant
        if debtor and creditor and debtor == creditor:
            raise ValidationError("Debtor and creditor cannot be the same")
        return cleaned_data

    def save(self, commit=True):
        obj = super().save(commit=False)  # type: Payment

        if not commit:
            return obj

        obj.save_with_entries(
            (
                Entry(
                    payment=obj,
                    participant=self.cleaned_data["debtor"],
                    amount=self.cleaned_data["amount"],
                ),
                Entry(
                    payment=obj,
                    participant=self.cleaned_data["creditor"],
                    amount=-self.cleaned_data["amount"],
                ),
            )
        )
        return obj
