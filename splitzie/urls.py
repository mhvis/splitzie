from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from splitzie import views

urlpatterns = [
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
            ]
        ),
    ),
    path("help/", views.HelpView.as_view(), name="help"),
    # path(
    #     "groups/<int:pk>/transactions/",
    #     views.TransactionListView.as_view(),
    #     name="transaction-list",
    # ),
    # path(
    #     "groups/<int:pk>/transactions/create/",
    #     views.TransactionTypeView.as_view(),
    #     name="transaction-create",
    # ),
    # path(
    #     "groups/<int:pk>/transactions/expense/",
    #     views.TransactionCreateExpenseView.as_view(),
    #     name="transaction-create-expense",
    # ),
    # path(
    #     "groups/<int:pk>/transactions/custom/",
    #     views.TransactionCreateCustomView.as_view(),
    #     name="transaction-create-custom",
    # ),
    # path(
    #     "groups/<int:pk>/transactions/settle/",
    #     views.TransactionCreateSettleView.as_view(),
    #     name="transaction-create-settle",
    # ),
    # path(
    #     "groups/<int:pk>/add/",
    #     views.GroupAddMemberView.as_view(),
    #     name="group-add-member",
    # ),
    # path(
    #     "groups/<int:pk>/join/<str:code>/",
    #     views.GroupJoinView.as_view(),
    #     name="group-join",
    # ),
    path("admin/", admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
