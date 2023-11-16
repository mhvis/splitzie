import decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import BadRequest
from django.db import transaction
from django.forms import modelform_factory
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import (
    TemplateView,
    ListView,
    DetailView,
    FormView,
)
from django.views.generic.detail import SingleObjectMixin

from groupsplit.forms import ExpenseForm, SettleForm
from groupsplit.models import Group, Expense, Participant, GroupEmail, Payment


class IndexView(TemplateView):
    template_name = "groupsplit/index.html"


class GroupMixin(SingleObjectMixin):
    model = Group
    slug_field = "code"
    context_object_name = "group"
    slug_url_kwarg = "code"


class GroupView(GroupMixin, DetailView):
    template_name = "groupsplit/group.html"


class GroupCreateView(View):
    def post(self, request, *args, **kwargs):
        group = Group.objects.create()
        url = reverse("group", args=(group.code,))

        response = render(request, "groupsplit/group.html", {"group": group})
        response.headers["HX-Push-Url"] = url
        return response


class GroupEditView(GroupMixin, DetailView):
    template_name = "groupsplit/group_form.html"

    def post(self, request, *args, **kwargs):
        group = self.object = self.get_object()
        action = request.POST.get("form")

        # Do the posted action
        if action == "name":
            form = modelform_factory(Group, fields=["name"])(
                request.POST, instance=group
            )
            if not form.is_valid():
                raise BadRequest
            form.save()
        elif action == "participant-create":
            form = modelform_factory(Participant, fields=["name"])(
                request.POST, instance=Participant(group=group)
            )
            if not form.is_valid():
                raise BadRequest
            form.save()
        elif action == "participant-delete":
            try:
                participant = Participant.objects.get(
                    group=group, pk=request.POST.get("participant")
                )
            except Participant.DoesNotExist:
                raise BadRequest
            participant.delete()
        elif action == "email-create":
            form = modelform_factory(GroupEmail, fields=["email"])(
                request.POST, instance=GroupEmail(group=group)
            )
            if not form.is_valid():
                raise BadRequest
            form.save()
        elif action == "email-delete":
            try:
                email = GroupEmail.objects.get(
                    group=group, pk=request.POST.get("email")
                )
            except GroupEmail.DoesNotExist:
                raise BadRequest
            email.delete()
        else:
            raise BadRequest

        if action == "name":
            return HttpResponse("Saved")
        else:
            return self.render_to_response(self.get_context_data())


class GroupSettleView(GroupMixin, DetailView):
    template_name = "groupsplit/group_settle.html"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = SettleForm(
            request.POST, instance=Payment(group=self.object, type="settle")
        )
        if form.is_valid():
            form.save()
            form = None  # Clear form so that there's no bound form in the response
        return self.render_to_response(self.get_context_data(form=form))


class ExpenseCreateView(GroupMixin, DetailView):
    template_name = "groupsplit/expense_form.html"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ExpenseForm(
            data=request.POST,
            files=request.FILES,
            instance=Expense(group=self.object, type="expense"),
        )
        if not form.is_valid():
            content = "".join(f"<li>{k}: {str(v)}" for k, v in form.errors.items())
            response = HttpResponse(f"<ul>{content}</ul>")
            response.headers["HX-Retarget"] = "form button[type=submit]"
            response.headers["HX-Reswap"] = "afterend"
            return response

        form.save()

        response = HttpResponse()
        response.headers["HX-Location"] = reverse(
            "group", kwargs={"code": self.object.code}
        )
        return response


class ExpenseDetailView(DetailView):
    model = Expense
    slug_url_kwarg = "code"
    slug_field = "group__code"
    query_pk_and_slug = True


class HelpView(TemplateView):
    template_name = "groupsplit/help.html"


#
#
# class GroupMixin(LoginRequiredMixin, SingleObjectMixin):
#     def get_object(self, queryset=None):
#         if queryset:
#             raise ValueError("Setting queryset is not supported.")
#         return super().get_object(queryset=Group.objects.filter(user=self.request.user))
#
#     def get(self, *args, **kwargs):
#         self.object = self.get_object()
#         return super().get(*args, **kwargs)
#
#
# class GroupDetailView(GroupMixin, DetailView):
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context.update(
#             {
#                 "join_url": (
#                         ("https" if self.request.is_secure() else "http")
#                         + "://"
#                         + self.request.get_host()
#                         + reverse(
#                     "group-join", args=[self.object.pk, self.object.join_code]
#                 )
#                 ),
#             }
#         )
#         return context
#
#
# class TransactionTypeView(GroupMixin, TemplateView):
#     template_name = "groupsplit/transaction_type.html"
#
#
# class TransactionCreateView(GroupMixin, TemplateView):
#     def get_forms(self):
#         """Returns a form for a transaction and a formset for the entries."""
#         instance = Transaction(group=self.object, created_by=self.request.user)
#         user_set = self.object.user_set.all()
#
#         form = TransactionForm(
#             data=self.request.POST if self.request.method == "POST" else None,
#             instance=instance,
#         )
#         form.fields["expense_user"].queryset = user_set
#
#         formset = EntryFormSet(
#             data=self.request.POST if self.request.method == "POST" else None,
#             initial=[{"user": u, "amount": decimal.Decimal("0.00")} for u in user_set],
#             instance=instance,
#         )
#         for f in formset:
#             f.fields["user"].queryset = user_set
#             f.fields["user"].disabled = True
#
#         return form, formset
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         form, formset = self.get_forms()
#         context.update({"form": form, "formset": formset})
#         return context
#
#     def post(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         form, formset = self.get_forms()
#         if form.is_valid() and formset.is_valid():
#             with transaction.atomic():
#                 tx = form.save()
#                 es = formset.save()
#             return redirect(self.object)
#         else:
#             context = self.get_context_data(
#                 object=self.object, form=form, formset=formset
#             )
#             return self.render_to_response(context)
#
#
# class TransactionCreateCustomView(TransactionCreateView):
#     template_name = "groupsplit/transaction_custom.html"
#
#     def get_forms(self):
#         form, formset = super().get_forms()
#         del form.fields["expense_user"]
#         del form.fields["expense_amount"]
#         return form, formset
#
#
# class TransactionCreateSettleView(TransactionCreateView):
#     template_name = "groupsplit/transaction_settle.html"
#     #
#     # def get_context_data(self, **kwargs):
#     #     context = super().get_context_data(**kwargs)
#     #     context.update({
#     #         "settle"
#     #     })
#
#
# class TransactionCreateExpenseView(GroupMixin, FormView):
#     template_name = "groupsplit/transaction_expense.html"
#     form_class = TransactionExpenseForm
#
#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs.update(
#             {
#                 "instance": Transaction(
#                     group=self.object,
#                     created_by=self.request.user,
#                     type="expense",
#                 )
#             }
#         )
#         return kwargs
#
#
# class GroupJoinView(LoginRequiredMixin, DetailView):
#     model = Group
#     template_name_suffix = "_join"
#
#     def get_queryset(self):
#         return super().get_queryset().filter(join_code=self.kwargs["code"])
#
#     def post(self, request, *args, **kwargs):
#         group = self.get_object()
#         group.user_set.add(self.request.user)
#         return redirect(group)
#
#
# class TransactionListView(GroupMixin, ListView):
#     # template_name = "groupsplit/transaction_list.html"
#     model = Transaction
#     # ordering = ("date",)
#     paginate_by = 20
#
#     def get_queryset(self):
#         return super().get_queryset().filter(group=self.object).order_by("-date")
#
#
# class GroupAddMemberView(GroupDetailView):
#     template_name = "groupsplit/group_add_member.html"
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context.update(
#             {
#                 "form": AddMemberForm(),
#             }
#         )
#         return context
#
