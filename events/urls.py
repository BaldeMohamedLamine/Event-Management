from django.urls import path
from . import views
from .views import revenue_data,user_articles,download_ticket,send_invitation,invitation_accept

app_name = 'events'

urlpatterns = [
    path("", views.EventListView.as_view(), name="list"),
    path('dashboard/', views.EventDashboardView.as_view(), name='dashboard'),
    path("create/", views.EventCreateView.as_view(), name="create"),
    path("<uuid:uid>/", views.EventDetailView.as_view(), name="detail"),
    path("<uuid:uid>/edit/", views.EventUpdateView.as_view(), name="edit"),
    path("<uuid:uid>/delete/", views.EventDeleteView.as_view(), name="delete"),
    path("<uuid:uid>/register/", views.EventRegistrationView.as_view(), name="register_event"),
    path("<uuid:uid>/payment/", views.PaymentView.as_view(), name="payment"),
    path("<uuid:uid>/participants/", views.ParticipantListView.as_view(), name="participants"),
    path("revenue-data/", revenue_data, name="revenue_data"),
    path('mes-articles/', user_articles, name='user_articles'),
    path("sales-details/", views.SalesDetailsView.as_view(), name="sales_details"),
    path("revenue-details/", views.RevenueDetailsView.as_view(), name="revenue_details"),
    path("payments-list/", views.PaymentsListView.as_view(), name="payments_list"),
    path('download-ticket/<uuid:ticket_uid>/', download_ticket, name='download_ticket'),
    path('invite/<uuid:uid>/', send_invitation, name='send_invitation'),
    path('invitation-accept/<str:token>/', invitation_accept, name='invitation_accept'),
    path('my-tickets/', views.MyTicketsView.as_view(), name='my_tickets'),
]
