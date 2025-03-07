import uuid
from datetime import datetime
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect,render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Event, Ticket, Payment,Invitation,Notification
from .forms import EventForm, EventFilterForm, PaymentForm, EventRegistrationForm
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from django.core.paginator import Paginator
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.http import HttpResponse, Http404
from django.contrib.sites.shortcuts import get_current_site
from .utils import generate_ticket_pdf
from django.utils.crypto import get_random_string


class EventCreateView(LoginRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/create_event.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not request.user.is_organisator(): 
            messages.error(request, "Vous n'avez pas accès à cette page.")
            return redirect(reverse_lazy('events:list'))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.organizer = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Événement créé avec succès.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Erreur lors de la création de l'événement. Vérifiez les champs.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('events:detail', kwargs={'uid': self.object.uid})

    def get_success_url(self):
        return reverse('events:detail', kwargs={'uid': self.object.uid})

class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'events/edit_event.html'
    slug_field = 'uid'
    slug_url_kwarg = 'uid'

    def test_func(self):
        event = self.get_object()
        return event.organizer == self.request.user

    def get_success_url(self):
        messages.success(self.request, "Événement mis à jour.")
        return reverse('events:detail', kwargs={'uid': self.object.uid})

class EventDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Event
    template_name = 'events/delete_event.html'
    slug_field = 'uid'
    slug_url_kwarg = 'uid'
    success_url = reverse_lazy('events:list')

    def test_func(self):
        event = self.get_object()
        return event.organizer == self.request.user

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Événement supprimé.")
        return super().delete(request, *args, **kwargs)


class EventListView(ListView):
    model = Event
    template_name = 'events/list_events.html'
    context_object_name = 'events'
    paginate_by = 4

    def get_queryset(self):
        qs = Event.objects.filter(start_date__gte=timezone.now()).order_by('start_date')
        self.filter_form = EventFilterForm(self.request.GET or None)
        if self.filter_form.is_valid():
            date = self.filter_form.cleaned_data.get('date')
            category = self.filter_form.cleaned_data.get('category')
            location = self.filter_form.cleaned_data.get('location')
            if date:
                qs = qs.filter(start_date__date=date)
            if category:
                qs = qs.filter(category=category)
            if location:
                qs = qs.filter(location__icontains=location)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.filter_form
        return context
    

class EventDashboardView(LoginRequiredMixin, UserPassesTestMixin ,ListView):
    model = Event
    template_name = 'events/dashboard.html'
    context_object_name = 'events'

    def test_func(self):
        return Event.objects.filter(organizer=self.request.user).exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_events'] = Event.objects.filter(organizer=self.request.user).count()
        context['total_participants'] = Ticket.objects.filter(event__organizer=self.request.user).values('user').distinct().count()
        
        ticket_sales = Ticket.objects.filter(event__organizer=self.request.user) \
                                     .annotate(month=TruncMonth('created_at')) \
                                     .values('month') \
                                     .annotate(total=Count('uid')) \
                                     .order_by('month')
        context['ticket_sales_labels'] = [
            item['month'].strftime('%b %Y') for item in ticket_sales if item['month']
        ]
        context['ticket_sales_values'] = [
            item['total'] for item in ticket_sales
        ]
        return context
@login_required
def revenue_data(request):

    if not Event.objects.filter(organizer=request.user).exists():
        return JsonResponse({'error': 'Accès refusé'}, status=403)
    revenue = Payment.objects.filter(ticket__event__organizer=request.user) \
                             .annotate(month=TruncMonth('payment_date')) \
                             .values('month') \
                             .annotate(total=Sum('amount')) \
                             .order_by('month')
    labels = [item['month'].strftime('%b %Y') for item in revenue if item['month']]
    values = [item['total'] for item in revenue]
    total_revenue = sum(values)
    data = {
        'labels': labels,
        'values': values,
        'total_revenue': total_revenue,
    }
    return JsonResponse(data)

@login_required
def user_dashboard(request):
    """Affiche les 5 derniers articles du user sur le dashboard"""
    articles = Event.objects.filter(organizer=request.user).order_by('end_date')[:5]
    return render(request, 'events/dashboard.html', {'articles': articles})

@login_required
def user_articles(request):
    """Affiche tous les articles du user avec pagination"""
    articles_list = Event.objects.filter(organizer=request.user).order_by('end_date')
    paginator = Paginator(articles_list, 10)  

    page_number = request.GET.get('page')
    articles = paginator.get_page(page_number)

    return render(request, 'events/user_articles.html', {'articles': articles})
    
class EventDetailView(DetailView):
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'
    slug_field = 'uid'
    slug_url_kwarg = 'uid'


class EventRegistrationView(LoginRequiredMixin, FormView):
    form_class = EventRegistrationForm
    template_name = 'events/register_event.html'

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, uid=self.kwargs.get('uid'))

        if self.event.is_private:
            token = request.GET.get('token')
            invitation = Invitation.objects.filter(event=self.event, token=token, used=False).first()

            if invitation:
                if self.event.tickets.filter(user=self.request.user).exists():
                    messages.error(self.request,"ℹ️ L'utilisateur est déjà inscrit, pas besoin d'utiliser l'invitation.")
                else:
                    messages.info(self.request,"Marquage de l'invitation comme utilisée...")
                invitation.used = True
                invitation.save()

        return super().dispatch(request, *args, **kwargs)


    def form_valid(self, form):
        if self.event.tickets.count() >= self.event.capacity:
            messages.error(self.request, "Cet événement est complet.")
            return redirect('events:detail', uid=self.event.uid)

        if self.event.tickets.filter(user=self.request.user).exists():
            messages.info(self.request, "Vous êtes déjà inscrit à cet événement.")
            return redirect('events:detail', uid=self.event.uid)

        if self.event.is_free:
            ticket = Ticket.objects.create(
                user=self.request.user,
                event=self.event,
                ticket_type='free',
                payment_status='completed'
            )

            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            ticket_url = self.request.build_absolute_uri(reverse('events:download_ticket', kwargs={'ticket_uid': ticket.uid}))
            qr.add_data(ticket_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            file_png = ContentFile(buffer.getvalue(), name=f"{ticket.uid}.png")
            ticket.qr_code.save(file_png.name, file_png)

            pdf_content = generate_ticket_pdf(ticket)

            email = EmailMessage(
                subject="Confirmation d'inscription à l'événement",
                body=(
                    f"Bonjour,\n\nVous êtes inscrit à l'événement '{self.event.title}'.\n"
                    f"Veuillez trouver ci-joint votre ticket contenant les informations de l'événement et votre code QR.\n\n"
                    "Cordialement,\nL'équipe de Gestion d'Événements"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[self.request.user.email],
            )
            email.attach(f"ticket_{ticket.uid}.pdf", pdf_content, "application/pdf")
            email.send()

            messages.success(self.request, "Inscription réussie pour l'événement gratuit. Un email contenant votre ticket a été envoyé.")
            return redirect('events:detail', uid=self.event.uid)
        else:
            return redirect('events:payment', uid=self.event.uid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.event
        return context
    

class PaymentView(LoginRequiredMixin, FormView):
    form_class = PaymentForm
    template_name = 'events/payment.html'

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, uid=self.kwargs.get('uid'))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        transaction_ref = uuid.uuid4().hex
        
        ticket = Ticket.objects.create(
            user=self.request.user,
            event=self.event,
            ticket_type='paid',
            payment_status='completed'
        )
        Payment.objects.create(
            user=self.request.user,
            ticket=ticket,
            amount=self.event.price,
            transaction_ref=transaction_ref
        )
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        ticket_url = self.request.build_absolute_uri(reverse('events:download_ticket', kwargs={'ticket_uid': ticket.uid}))
        qr.add_data(ticket_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        file_png = ContentFile(buffer.getvalue(), name=f"{ticket.uid}.png")
        ticket.qr_code.save(file_png.name, file_png)

        pdf_content = generate_ticket_pdf(ticket)

        email = EmailMessage(
            subject="Confirmation d'achat de billet",
            body=(
                f"Bonjour,\n\nVotre paiement pour l'événement '{self.event.title}' a été validé.\n"
                f"Veuillez trouver ci-joint votre ticket contenant les informations de l'événement et votre code QR.\n\n"
                "Cordialement,\nL'équipe de Gestion d'Événements"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[self.request.user.email],
        )
        email.attach(f"ticket_{ticket.uid}.pdf", pdf_content, "application/pdf")
        email.send()

        messages.success(self.request, "Paiement effectué et inscription confirmée. Un email contenant votre ticket a été envoyé.")
        return redirect('events:detail', uid=self.event.uid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.event
        return context


@login_required
def download_ticket(request, ticket_uid):
    ticket = get_object_or_404(Ticket, uid=ticket_uid, user=request.user)
    if not ticket.qr_code:
        raise Http404("Ticket introuvable.")
    with open(ticket.qr_code.path, 'rb') as f:
        response = HttpResponse(f.read(), content_type="image/png")
        response['Content-Disposition'] = f'attachment; filename="{ticket.uid}.png"'
        return response

class ParticipantListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Ticket
    template_name = 'events/participants_list.html'
    context_object_name = 'tickets'

    def test_func(self):
        self.event = get_object_or_404(Event, uid=self.kwargs.get('uid'))
        return self.event.organizer == self.request.user

    def get_queryset(self):
        return Ticket.objects.filter(event=self.event)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.event
        return context


@login_required
def send_invitation(request, uid):
    event = get_object_or_404(Event, uid=uid)

    if request.method == "POST":
        email = request.POST.get("email")
        message = request.POST.get("message", "")

        token = get_random_string(64)

        Invitation.objects.create(event=event, email=email, token=token)

        current_site = get_current_site(request)
        invitation_link = f"http://{current_site.domain}/events/{event.uid}/register/?token={token}"

        email_body = f"""
        Vous êtes invité(e) à l'événement : {event.title}
        Date : {event.start_date.strftime('%d/%m/%Y %H:%M')}
        Lieu : {event.location}

        Message de l'organisateur : {message}

        Cliquez sur le lien pour vous inscrire : {invitation_link}
        """

        send_mail(
            subject=f"Invitation à l'événement : {event.title}",
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

        messages.success(request, "Invitation envoyée avec succès !")
        return redirect("events:detail", uid=event.uid)

    return render(request, "events/send_invitation.html", {"event": event})

def invitation_accept(request, token):
    invitation = get_object_or_404(Invitation, token=token, used=False)
    invitation.used = True
    invitation.save()
    messages.success(request, f"Vous êtes invité à {invitation.event.title}. Veuillez vous inscrire via cette page.")
    return redirect('events:register_event', uid=invitation.event.uid)




class SalesDetailsView(ListView):
    model = Payment
    template_name = 'events/sales_details.html'
    context_object_name = 'payments'
    paginate_by = 20 

    def get_queryset(self):
        queryset = super().get_queryset()
        
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                queryset = queryset.filter(payment_date__gte=start_date_obj)
            except ValueError:
                pass
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                queryset = queryset.filter(payment_date__lte=end_date_obj)
            except ValueError:
                pass

        order = self.request.GET.get('order')
        if order in ['payment_date', '-payment_date', 'amount', '-amount']:
            queryset = queryset.order_by(order)
        else:
            queryset = queryset.order_by('-payment_date') 

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_sales'] = self.get_queryset().count()
        context['total_revenue'] = self.get_queryset().aggregate(total=Sum('amount'))['total'] or 0

        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['order'] = self.request.GET.get('order', '')
        return context

class RevenueDetailsView(ListView):
    model = Payment
    template_name = 'events/revenue_details.html'
    context_object_name = 'payments'
    paginate_by = 20 

    def get_queryset(self):
        return Payment.objects.all().order_by('-payment_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_revenue'] = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
        return context

class PaymentsListView(ListView):
    model = Payment
    template_name = 'events/payments_list.html'
    context_object_name = 'payments'
    paginate_by = 20  

    def get_queryset(self):
        return Payment.objects.all().order_by('-payment_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_revenue'] = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
        return context

class MyTicketsView(LoginRequiredMixin, ListView):
    model = Ticket
    template_name = 'events/my_tickets.html'
    context_object_name = 'tickets'
    
    def get_queryset(self):
        return Ticket.objects.filter(user=self.request.user).order_by('-created_at')



# def inscrire_utilisateur(request, uid):
#     event = Event.objects.get(uid=uid)
#     if event and not event.participants.filter(uid=request.user.uid).exists():
#         event.participants.add(request.user)
#         notification_message = f"Vous êtes maintenant inscrit à l'événement {event.name}."
#         Notification.objects.create(
#             user=request.user,
#             title=f"Inscription réussie à {event.name}",
#             message=notification_message,
#             is_read=False
#         )
#     return redirect('event_detail', uid=event.uid)


# def modifier_evenement(request, uid):
#     event = Event.objects.get(uid=uid)
#     if request.method == 'POST':
#         event.name = request.POST['name']
#         event.description = request.POST['description']
#         event.save()

#         for participant in event.participants.all():
#             notification_message = f"L'événement {event.name} a été modifié."
#             Notification.objects.create(
#                 user=participant,
#                 title=f"Modification de l'événement {event.name}",
#                 message=notification_message,
#                 is_read=False
#             )
#     return redirect('event_detail', uid=event.uid)


# def annuler_evenement(request, uid):
#     event = Event.objects.get(uid=uid)
#     event.is_active = False 
#     event.save()

#     for participant in event.participants.all():
#         notification_message = f"L'événement {event.name} a été annulé."
#         Notification.objects.create(
#             user=participant,
#             title=f"Annulation de l'événement {event.name}",
#             message=notification_message,
#             is_read=False
#         )
#     return redirect('event_list')


# def inscrire_participant(request, uid):
#     event = Event.objects.get(uid=uid)
#     if event:
#         event.participants.add(request.user)
#         notification_message = f"Un nouveau participant ({request.user.username}) s'est inscrit à l'événement {event.name}."
#         Notification.objects.create(
#             user=event.organizer,
#             title=f"Nouvelle inscription à {event.name}",
#             message=notification_message,
#             is_read=False
#         )
#     return redirect('event_detail', event_id=event.uid)

# def envoyer_rappel(event):
#     now = timezone.now()
#     if event.event_date - timedelta(hours=24) <= now <= event.event_date:
#         for participant in event.participants.all():
#             notification_message = f"Rappel : L'événement {event.name} approche dans moins de 24h."
#             Notification.objects.create(
#                 user=participant,
#                 title=f"Rappel pour {event.name}",
#                 message=notification_message,
#                 is_read=False
#             )

# def gestion_erreur(request):
#     try:
#         pass
#     except Exception as e:
#         notification_message = f"Une erreur s'est produite : {str(e)}"
#         Notification.objects.create(
#             user=request.user,
#             title="Erreur système",
#             message=notification_message,
#             is_read=False
#         )
#     return redirect('error_page')




