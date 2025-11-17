from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from datetime import timedelta
import hashlib
import stripe
import json
import logging
import requests
from .models import Course, Instructor, Booking, PricingTier, PaymentPlan, CoursePayment, StripePaymentRecord
from .forms import BookingForm

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)


def verify_turnstile(token, remote_ip):
    """
    Verify Cloudflare Turnstile token.
    Returns True if verification succeeds, False otherwise.
    """
    secret_key = getattr(settings, 'TURNSTILE_SECRET_KEY', None)

    # Skip verification if no secret key is configured (development)
    if not secret_key:
        logger.warning("Turnstile verification skipped - no secret key configured")
        return True

    try:
        response = requests.post(
            'https://challenges.cloudflare.com/turnstile/v0/siteverify',
            data={
                'secret': secret_key,
                'response': token,
                'remoteip': remote_ip,
            },
            timeout=5
        )

        result = response.json()
        return result.get('success', False)
    except Exception as e:
        logger.error(f"Turnstile verification error: {str(e)}")
        # Fail closed - reject on error
        return False


def home(request):
    try:
        featured_courses = Course.objects.filter(is_active=True)[:3]
        context = {
            'featured_courses': featured_courses
        }
        return render(request, 'home.html', context)
    except Exception as e:
        # Fallback for database issues
        from django.http import HttpResponse
        return HttpResponse(f"<h1>Hortus Cognitor - Django is working!</h1><p>Database issue: {str(e)}</p>")

def about(request):
    return render(request, 'about.html')

def privacy_policy(request):
    """Display the privacy policy page"""
    from datetime import datetime
    return render(request, 'privacy_policy.html', {
        'last_updated': 'January 2026'
    })

def regenerative_movement_course(request):
    return render(request, 'regenerative_movement_course.html')

def contact(request):
    # Pass Turnstile site key to template
    context = {
        'TURNSTILE_SITE_KEY': getattr(settings, 'TURNSTILE_SITE_KEY', '')
    }

    if request.method == 'POST':
        # Rate limiting - max 3 contact attempts per 5 minutes per IP
        if is_rate_limited(request, 'contact', limit=3, window=300):
            messages.error(request, 'Too many contact attempts. Please wait 5 minutes before trying again.')
            return redirect('contact')

        # Verify Cloudflare Turnstile
        turnstile_response = request.POST.get('cf-turnstile-response', '')
        remote_ip = request.META.get('REMOTE_ADDR', '')

        if not verify_turnstile(turnstile_response, remote_ip):
            messages.error(request, 'Please complete the verification challenge.')
            return redirect('contact')

        # Get and sanitize form data
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        # Basic validation
        if not name or not email or not subject or not message:
            messages.error(request, 'Please fill in all required fields.')
            return redirect('contact')

        # Validate subject length and content
        if len(subject) > 200:
            messages.error(request, 'Subject line is too long (maximum 200 characters).')
            return redirect('contact')

        try:
            # Create a booking record - this will run full model validation
            booking = Booking(
                course=None,  # Contact form doesn't relate to a specific course
                full_name=name,
                email=email,
                phone=phone,
                message=f"Subject: {subject}\n\n{message}",
            )
            # Run model validation (will raise ValidationError if invalid)
            booking.full_clean()
            booking.save()

            # Send email notification to Hannah
            send_contact_form_notification(booking, subject)

            messages.success(request, 'Thank you for your message! We will get back to you within 24-48 hours.')
            return redirect('contact')
        except ValidationError as e:
            # Handle validation errors
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f'{field.replace("_", " ").title()}: {error}')
            return redirect('contact')
        except Exception as e:
            logger.error(f"Error saving contact form: {str(e)}")
            messages.error(request, 'There was an error sending your message. Please try again.')
            return redirect('contact')

    return render(request, 'contact.html', context)

class CourseListView(ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    
    def get_queryset(self):
        return Course.objects.filter(is_active=True)

class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['booking_form'] = BookingForm()
        return context

def get_client_ip(request):
    """Get client IP address for rate limiting"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def is_rate_limited(request, action='booking', limit=3, window=300):
    """
    Rate limiting function
    - limit: max attempts per window
    - window: time window in seconds (default 5 minutes)
    """
    ip = get_client_ip(request)
    cache_key = f'rate_limit_{action}_{ip}'
    
    attempts = cache.get(cache_key, 0)
    if attempts >= limit:
        return True
    
    cache.set(cache_key, attempts + 1, window)
    return False

def book_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    
    if request.method == 'POST':
        # Rate limiting - max 3 booking attempts per 5 minutes per IP
        if is_rate_limited(request, 'booking', limit=3, window=300):
            messages.error(request, 'Too many booking attempts. Please wait 5 minutes before trying again.')
            return redirect('course_detail', slug=course.slug)
        
        form = BookingForm(request.POST)
        if form.is_valid():
            try:
                booking = form.save(commit=False)
                booking.course = course
                booking.save()
                messages.success(request, f'Thank you for booking {course.title}! We will contact you soon.')
                return redirect('course_detail', slug=course.slug)
            except Exception as e:
                messages.error(request, 'There was an error processing your booking. Please try again.')
                return redirect('course_detail', slug=course.slug)
        else:
            # Form validation failed
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.replace("_", " ").title()}: {error}')
    else:
        form = BookingForm()
    
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'booking_form': form
    })


def payment_selection(request, slug):
    """Display the three-tier pricing and payment plan selection page"""
    course = get_object_or_404(Course, slug=slug, is_active=True)
    pricing_tiers = course.pricing_tiers.all().order_by('price')
    payment_plans = PaymentPlan.objects.filter(is_active=True)
    
    context = {
        'course': course,
        'pricing_tiers': pricing_tiers,
        'payment_plans': payment_plans,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    }
    return render(request, 'courses/payment_selection.html', context)


def create_checkout_session(request):
    """Create Stripe Checkout session for course payment"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    # Rate limiting - max 5 payment attempts per 10 minutes per IP
    if is_rate_limited(request, 'payment', limit=5, window=600):
        return JsonResponse({
            'error': 'Too many payment attempts. Please wait 10 minutes before trying again.'
        }, status=429)

    try:
        data = json.loads(request.body)
        course_id = data.get('course_id')
        pricing_tier_id = data.get('pricing_tier_id')
        payment_plan_id = data.get('payment_plan_id')
        customer_details = data.get('customer_details', {})
        
        # Get objects
        course = get_object_or_404(Course, id=course_id)
        pricing_tier = get_object_or_404(PricingTier, id=pricing_tier_id, course=course)
        payment_plan = get_object_or_404(PaymentPlan, id=payment_plan_id)
        
        # Create booking
        booking = Booking.objects.create(
            course=course,
            full_name=customer_details.get('full_name', ''),
            email=customer_details.get('email', ''),
            phone=customer_details.get('phone', ''),
            message=customer_details.get('message', ''),
        )
        
        # Create course payment record
        course_payment = CoursePayment.objects.create(
            booking=booking,
            pricing_tier=pricing_tier,
            payment_plan=payment_plan,
        )
        
        # Determine payment amount (deposit for installments, full for one-time)
        if payment_plan.name == 'installment':
            amount = course_payment.deposit_amount
            payment_type = 'deposit'
        else:
            amount = course_payment.total_amount
            payment_type = 'full'
        
        # Create Stripe Checkout Session with Connect account
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': settings.PAYMENT_CURRENCY,
                    'product_data': {
                        'name': f"{course.title} - {pricing_tier.get_tier_display()}",
                        'description': f"{payment_type.title()} Payment - {pricing_tier.description[:100]}...",
                    },
                    'unit_amount': int(float(amount) * 100),  # Convert to pence
                },
                'quantity': 1,
            }],
            metadata={
                'course_payment_id': course_payment.id,
                'payment_type': payment_type,
                'booking_id': booking.id,
            },
            mode='payment',
            success_url=request.build_absolute_uri(reverse('payment_success')) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri(reverse('payment_cancel')),
            customer_email=customer_details.get('email'),
        )
        
        # Update course payment with Stripe session info (payment_intent is created later)
        if checkout_session.payment_intent:
            course_payment.stripe_payment_intent_id = checkout_session.payment_intent
            course_payment.save()
        
        return JsonResponse({'checkout_url': checkout_session.url})
        
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)


def send_course_confirmation_email(course_payment):
    """
    Send course confirmation email after successful payment.

    Args:
        course_payment: CoursePayment instance
    """
    try:
        booking = course_payment.booking
        course = booking.course

        # Email context
        context = {
            'booking': booking,
            'course': course,
            'payment': course_payment,
        }

        # Render HTML and text versions
        html_content = render_to_string('emails/course_confirmation.html', context)
        text_content = render_to_string('emails/course_confirmation.txt', context)

        # Create email
        subject = f'Course Booking Confirmation - {course.title}'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = booking.email

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[to_email],
        )
        email.attach_alternative(html_content, "text/html")

        # Send email
        email.send(fail_silently=False)
        logger.info(f"Course confirmation email sent to {to_email} for booking #{booking.id}")

    except Exception as e:
        logger.error(f"Error sending course confirmation email: {str(e)}")


def send_admin_booking_notification(course_payment):
    """
    Send notification email to Hannah when a new booking is made.

    Args:
        course_payment: CoursePayment instance
    """
    try:
        from .models import SiteSettings

        booking = course_payment.booking
        course = booking.course

        # Get notification email addresses from settings
        site_settings = SiteSettings.load()
        admin_emails = site_settings.get_notification_emails()

        if not admin_emails:
            logger.warning(f"No notification emails configured in Site Settings for booking #{booking.id}")
            return

        # Email context
        context = {
            'booking': booking,
            'course': course,
            'payment': course_payment,
        }

        # Render HTML and text versions
        html_content = render_to_string('emails/admin_booking_notification.html', context)
        text_content = render_to_string('emails/admin_booking_notification.txt', context)

        # Create email
        subject = f'New Booking Received - {course.title}'
        from_email = settings.DEFAULT_FROM_EMAIL

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=admin_emails,
        )
        email.attach_alternative(html_content, "text/html")

        # Send email
        email.send(fail_silently=False)
        logger.info(f"Admin booking notification sent to {', '.join(admin_emails)} for booking #{booking.id}")

    except Exception as e:
        logger.error(f"Error sending admin booking notification: {str(e)}")


def send_contact_form_notification(booking, subject):
    """
    Send notification email to Hannah when a contact form is submitted.

    Args:
        booking: Booking instance (with course=None for contact forms)
        subject: The subject line from the contact form
    """
    try:
        # Sanitize subject to prevent email header injection
        # Remove newlines, carriage returns, and null bytes
        sanitized_subject = subject.replace('\n', ' ').replace('\r', ' ').replace('\0', ' ')
        # Truncate to reasonable length
        sanitized_subject = sanitized_subject[:200]

        # Email context
        context = {
            'booking': booking,
            'subject': sanitized_subject,
        }

        # Render email content
        email_body = f"""HORTUS COGNITOR
Contact Form Submission

A new contact form message has been received.

CONTACT DETAILS
----------------
Name: {booking.full_name}
Email: {booking.email}
Phone: {booking.phone or 'Not provided'}
Submitted: {booking.created_at.strftime('%d %B %Y, %H:%M')}

SUBJECT
-------
{sanitized_subject}

MESSAGE
-------
{booking.message.replace(f'Subject: {subject}', '').strip()}

---
View in Admin Panel: https://hortuscognitor.onrender.com/admin/courses/booking/{booking.id}/change/
Hortus Cognitor Contact Form Notification
"""

        # Create email
        subject_line = f'New Contact Form - {sanitized_subject}'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = 'hannah@hortuscognitor.co.uk'

        email = EmailMultiAlternatives(
            subject=subject_line,
            body=email_body,
            from_email=from_email,
            to=[to_email],
        )

        # Send email
        email.send(fail_silently=False)
        logger.info(f"Contact form notification sent to {to_email} for booking #{booking.id}")

    except Exception as e:
        logger.error(f"Error sending contact form notification: {str(e)}")


def payment_success(request):
    """Handle successful payment"""
    session_id = request.GET.get('session_id')

    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            course_payment_id = session.metadata.get('course_payment_id')
            payment_type = session.metadata.get('payment_type')

            if course_payment_id:
                course_payment = CoursePayment.objects.get(id=course_payment_id)

                # Update payment status
                if payment_type == 'deposit':
                    course_payment.status = 'deposit_paid'
                    course_payment.deposit_paid_at = timezone.now()
                elif payment_type == 'full':
                    course_payment.status = 'fully_paid'
                    course_payment.deposit_paid_at = timezone.now()
                    course_payment.final_paid_at = timezone.now()

                # Update payment intent ID if available
                if session.payment_intent:
                    course_payment.stripe_payment_intent_id = session.payment_intent

                course_payment.save()

                # Create payment record
                StripePaymentRecord.objects.create(
                    course_payment=course_payment,
                    payment_type=payment_type,
                    stripe_payment_intent_id=session.payment_intent,
                    amount=session.amount_total / 100,  # Convert from pence
                    status='succeeded',
                    processed_at=timezone.now(),
                )

                # Send confirmation email to customer
                send_course_confirmation_email(course_payment)

                # Send notification email to Hannah
                send_admin_booking_notification(course_payment)

                context = {
                    'course_payment': course_payment,
                    'session': session,
                    'payment_type': payment_type,
                }
                return render(request, 'courses/payment_success.html', context)

        except Exception as e:
            logger.error(f"Error processing successful payment: {str(e)}")
            messages.error(request, 'There was an error processing your payment confirmation.')

    return render(request, 'courses/payment_success.html', {})


def payment_cancel(request):
    """Handle cancelled payment"""
    messages.info(request, 'Payment was cancelled. You can try again anytime.')
    return render(request, 'courses/payment_cancel.html', {})


@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks with idempotency and proper error handling"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Stripe webhook invalid payload: {str(e)}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Stripe webhook signature verification failed: {str(e)}")
        return HttpResponse(status=400)

    # Get event ID for idempotency checking
    event_id = event.get('id')
    event_type = event.get('type')

    logger.info(f"Received Stripe webhook: {event_type} (ID: {event_id})")

    # Handle the event
    if event_type == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        payment_intent_id = payment_intent['id']

        try:
            # Check if we've already processed this payment
            existing_record = StripePaymentRecord.objects.filter(
                stripe_payment_intent_id=payment_intent_id
            ).first()

            if existing_record:
                logger.info(f"Payment {payment_intent_id} already processed (idempotent)")
                return HttpResponse(status=200)

            # Find the associated course payment
            course_payment = CoursePayment.objects.filter(
                stripe_payment_intent_id=payment_intent_id
            ).first()

            if course_payment:
                # Update payment status based on metadata
                if course_payment.status == 'pending':
                    course_payment.status = 'deposit_paid'
                    course_payment.deposit_paid_at = timezone.now()
                elif course_payment.status == 'deposit_paid':
                    course_payment.status = 'fully_paid'
                    course_payment.final_paid_at = timezone.now()

                course_payment.save()
                logger.info(f"Updated CoursePayment {course_payment.id} status to {course_payment.status}")
            else:
                logger.warning(f"No CoursePayment found for payment_intent {payment_intent_id}")

        except Exception as e:
            logger.error(f"Error processing payment_intent.succeeded webhook: {str(e)}")
            return HttpResponse(status=500)

    elif event_type == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        payment_intent_id = payment_intent['id']
        error_message = payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')

        logger.error(f"Payment failed: {payment_intent_id} - {error_message}")

        try:
            # Update course payment status to indicate failure
            course_payment = CoursePayment.objects.filter(
                stripe_payment_intent_id=payment_intent_id
            ).first()

            if course_payment:
                # Don't change status to failed automatically - keep as pending
                # This allows customers to retry with the same booking
                logger.warning(f"Payment failed for CoursePayment {course_payment.id}: {error_message}")

        except Exception as e:
            logger.error(f"Error processing payment_intent.payment_failed webhook: {str(e)}")

    else:
        logger.info(f"Unhandled webhook event type: {event_type}")

    return HttpResponse(status=200)


def instagram_course_poster(request, slug):
    """
    Render Instagram poster for course announcement.
    Access at /instagram/course/{slug}/
    """
    course = get_object_or_404(Course, slug=slug)
    return render(request, 'instagram/course_announcement.html', {
        'course': course
    })