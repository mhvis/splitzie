from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from splitzie.models import Expense, Participant, Entry, Payment


class ExpenseForm(forms.ModelForm):
    type = forms.ChoiceField(choices=[("expense", "Expense"), ("income", "Income")])
    amount = forms.DecimalField(
        max_digits=7, decimal_places=2, min_value=Decimal("0.00")
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
