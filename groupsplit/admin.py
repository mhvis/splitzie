from django.contrib import admin

from groupsplit import models


class ParticipantInline(admin.TabularInline):
    model = models.Participant


@admin.register(models.Group)
class GroupAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    ordering = ("name",)
    inlines = [ParticipantInline]


class EntryInline(admin.TabularInline):
    model = models.Entry


@admin.register(models.Payment)
class PaymentAdmin(admin.ModelAdmin):
    inlines = [EntryInline]


@admin.register(models.Expense)
class ExpenseAdmin(admin.ModelAdmin):
    inlines = [EntryInline]
