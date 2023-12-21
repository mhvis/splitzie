import base64
import io
import random

import qrcode
import qrcode.image.svg
from django.conf import settings
from django.core.exceptions import BadRequest
from django.db import transaction
from django.forms import modelform_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import get_language
from django.views import View
from django.views.generic import (
    TemplateView,
    DetailView,
)
from django.views.generic.detail import SingleObjectMixin

from splitzie.forms import ExpenseForm, SettleForm
from splitzie.mail import send_rendered_mail
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


class GroupTableView(GroupMixin, DetailView):
    template_name = "splitzie/group_table.html"


class GroupCreateView(View):
    def post(self, request, *args, **kwargs):
        group = Group.objects.create()
        url = reverse("group", args=(group.code,))

        if request.headers.get("HX-Request"):
            response = render(request, "splitzie/group.html", {"group": group})
            response.headers["HX-Push-Url"] = url
        else:
            response = HttpResponseRedirect(url)
        return response


class GroupEditView(GroupMixin, DetailView):
    template_name = "splitzie/group_form.html"

    def get_qr_svg(self) -> str:
        # Deprecated: use PNG
        if not self.object:
            raise ValueError("Group missing")
        url = self.request.build_absolute_uri(
            reverse("group", kwargs={"code": self.object.code})
        )

        qr = qrcode.QRCode(
            version=None,
            image_factory=qrcode.image.svg.SvgPathImage,
            box_size=10,
        )
        qr.add_data(url)
        qr.make(fit=True)
        return qr.make_image().to_string(encoding="unicode")

    def get_qr_png_uri(self) -> str:
        if not self.object:
            raise ValueError("Group missing")
        url = settings.BASE_URL + reverse("group", kwargs={"code": self.object.code})

        qr = qrcode.QRCode(
            box_size=5,
            border=5,
        )
        qr.add_data(url)
        qr.make()
        img = qr.make_image()
        buffered = io.BytesIO()
        img.save(buffered)
        data = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{data}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                # "qr_svg": mark_safe(self.get_qr_svg()),
                "qr_png_uri": mark_safe(self.get_qr_png_uri()),
            }
        )
        return context

    def handle_name(self):
        form = modelform_factory(Group, fields=["name"])(
            self.request.POST, instance=self.object
        )
        if not form.is_valid():
            raise BadRequest
        form.save()

    def handle_participant_create(self):
        form = modelform_factory(Participant, fields=["name"])(
            self.request.POST, instance=Participant(group=self.object)
        )
        if not form.is_valid():
            raise BadRequest
        form.save()

    def handle_participant_delete(self):
        try:
            participant = Participant.objects.get(
                group=self.object, pk=self.request.POST.get("participant")
            )
        except Participant.DoesNotExist:
            raise BadRequest
        participant.delete()

    def handle_email_create(self):
        form = modelform_factory(LinkedEmail, fields=["email"])(
            self.request.POST,
            instance=LinkedEmail(group=self.object, language=get_language()),
        )
        if not form.is_valid():
            raise BadRequest
        with transaction.atomic():
            linked_email = form.save()  # type: LinkedEmail
            linked_email.send_mail(
                "splitzie/mails/email_added.txt",
                "splitzie/mails/email_added_subject.txt",
                {"group": self.object},
            )

    def handle_email_delete(self):
        try:
            email = LinkedEmail.objects.get(
                group=self.object, pk=self.request.POST.get("email")
            )
        except LinkedEmail.DoesNotExist:
            raise BadRequest
        with transaction.atomic():
            email.delete()
            email.send_mail(
                "splitzie/mails/email_removed.txt",
                "splitzie/mails/email_removed_subject.txt",
                {"group": self.object},
            )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = request.POST.get("form")

        # Do the posted action
        if action == "name":
            self.handle_name()
        elif action == "participant-create":
            self.handle_participant_create()
        elif action == "participant-delete":
            self.handle_participant_delete()
        elif action == "email-create":
            self.handle_email_create()
        elif action == "email-delete":
            self.handle_email_delete()
        else:
            raise BadRequest

        return self.render_to_response(self.get_context_data())


class EmailDeleteView(View):
    pass


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Shuffle participants, to use for the expense form
        participants = list(self.object.participants.all())
        random.shuffle(participants)
        context.update(
            {
                "participants_shuffle": participants,
            }
        )
        return context

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
