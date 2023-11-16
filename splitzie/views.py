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

from splitzie.forms import ExpenseForm, SettleForm
from splitzie.models import Group, Expense, Participant, LinkedEmail, Payment


class IndexView(TemplateView):
    template_name = "splitzie/index.html"


class GroupMixin(SingleObjectMixin):
    model = Group
    slug_field = "code"
    context_object_name = "group"
    slug_url_kwarg = "code"


class GroupView(GroupMixin, DetailView):
    template_name = "splitzie/group.html"


class GroupCreateView(View):
    def post(self, request, *args, **kwargs):
        group = Group.objects.create()
        url = reverse("group", args=(group.code,))

        response = render(request, "splitzie/group.html", {"group": group})
        response.headers["HX-Push-Url"] = url
        return response


class GroupEditView(GroupMixin, DetailView):
    template_name = "splitzie/group_form.html"

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
            form = modelform_factory(LinkedEmail, fields=["email"])(
                request.POST, instance=LinkedEmail(group=group)
            )
            if not form.is_valid():
                raise BadRequest
            form.save()
        elif action == "email-delete":
            try:
                email = LinkedEmail.objects.get(
                    group=group, pk=request.POST.get("email")
                )
            except LinkedEmail.DoesNotExist:
                raise BadRequest
            email.delete()
        else:
            raise BadRequest

        if action == "name":
            return HttpResponse("Saved")
        else:
            return self.render_to_response(self.get_context_data())


class GroupSettleView(GroupMixin, DetailView):
    template_name = "splitzie/group_settle.html"

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
    template_name = "splitzie/expense_form.html"

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
    template_name = "splitzie/help.html"
