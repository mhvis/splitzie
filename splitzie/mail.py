from django.core.mail import send_mail
from django.template import loader


def send_rendered_mail(
    email_template_name: str,
    subject_template_name: str,
    recipient_list: list[str],
    context: dict = None,
):
    # if context is None:
    #     context = {}

    subject = loader.render_to_string(subject_template_name, context)
    message = loader.render_to_string(email_template_name, context)

    send_mail(subject, message, None, recipient_list)
