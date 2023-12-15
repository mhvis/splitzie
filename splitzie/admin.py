from django.contrib import admin

from splitzie import models


class ParticipantInline(admin.TabularInline):
    model = models.Participant


class EmailInline(admin.TabularInline):
    model = models.LinkedEmail


@admin.register(models.Group)
class GroupAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    ordering = ("name",)
    readonly_fields = ("created_at",)
    inlines = [ParticipantInline, EmailInline]


class EntryInline(admin.TabularInline):
    model = models.Entry


@admin.register(models.Payment)
class PaymentAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at",)
    inlines = [EntryInline]


@admin.register(models.Expense)
class ExpenseAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at",)
    inlines = [EntryInline]
