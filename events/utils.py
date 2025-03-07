# utils.py
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

def generate_ticket_pdf(ticket):
    """
    Génère un PDF contenant les informations de l'événement et le QR code du ticket.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Titre du ticket
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 50, f"Ticket pour {ticket.event.title}")

    # Informations sur l'événement
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 100, f"Événement: {ticket.event.title}")
    c.drawString(50, height - 120, f"Lieu: {ticket.event.location}")
    c.drawString(50, height - 140, f"Date de début: {ticket.event.start_date.strftime('%d/%m/%Y %H:%M')}")
    c.drawString(50, height - 160, f"Date de fin: {ticket.event.end_date.strftime('%d/%m/%Y %H:%M')}")
    c.drawString(50, height - 180, f"Organisateur: {ticket.event.organizer.get_full_name() or ticket.event.organizer.username}")

    # Affichage du QR code s'il est disponible
    if ticket.qr_code:
        try:
            qr_image = ImageReader(ticket.qr_code.path)
            c.drawImage(qr_image, width - 150, height - 250, width=100, height=100)
        except Exception as e:
            c.drawString(50, height - 200, "Erreur lors de l'affichage du QR code.")
    c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
