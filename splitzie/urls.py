import pprint

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse, HttpRequest
from django.urls import path, include

from splitzie import views


def return_request_headers(request: HttpRequest):
    response = HttpResponse(
        pprint.pformat(dict(request.headers))
        + "\nis_secure: "
        + str(request.is_secure())
    )
    # pprint.pprint(dict(request.headers))
    response.headers["Content-Type"] = "text/plain"
    #
    return response


urlpatterns = i18n_patterns(
    path("", views.IndexView.as_view(), name="index"),
    path("groups/create/", views.GroupCreateView.as_view(), name="group-create"),
    path(
        "groups/<code>/",
        include(
            [
                path("", views.GroupView.as_view(), name="group"),
                path("edit/", views.GroupEditView.as_view(), name="group-edit"),
                path("add/", views.ExpenseCreateView.as_view(), name="expense-create"),
                path("settle/", views.GroupSettleView.as_view(), name="group-settle"),
                path(
                    "expense/<int:pk>/",
                    views.ExpenseDetailView.as_view(),
                    name="expense",
                ),
                path(
                    "deletemail/<int:pk>/",
                    views.EmailDeleteView.as_view(),
                    name="email-delete",
                ),
                path("table/", views.GroupTableView.as_view(), name="group-table"),
            ]
        ),
    ),
    path("help/", views.HelpView.as_view(), name="help"),
    path("admin/", admin.site.urls),
)

urlpatterns += (
    path("i18n/", include("django.conf.urls.i18n")),
    path("headers/", return_request_headers),
)

# Only used in DEBUG mode to serve media files
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
