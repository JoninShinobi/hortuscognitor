from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
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
from .models import Course, Instructor, Booking, PricingTier, PaymentPlan, CoursePayment, StripePaymentRecord
from .forms import BookingForm

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)

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

def regenerative_movement_course(request):
    return render(request, 'regenerative_movement_course.html')

def contact(request):
    if request.method == 'POST':
        # Rate limiting - max 3 contact attempts per 5 minutes per IP
        if is_rate_limited(request, 'contact', limit=3, window=300):
            messages.error(request, 'Too many contact attempts. Please wait 5 minutes before trying again.')
            return redirect('contact')
        
        # Get form data
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        # Basic validation
        if not name or not email or not subject or not message:
            messages.error(request, 'Please fill in all required fields.')
            return redirect('contact')
        
        try:
            # Create a booking record (reusing the existing model for simplicity)
            booking = Booking.objects.create(
                course=None,  # Contact form doesn't relate to a specific course
                full_name=name,
                email=email,
                phone=phone,
                message=f"Subject: {subject}\n\n{message}",
            )
            messages.success(request, 'Thank you for your message! We will get back to you within 24-48 hours.')
            return redirect('contact')
        except Exception as e:
            logger.error(f"Error saving contact form: {str(e)}")
            messages.error(request, 'There was an error sending your message. Please try again.')
            return redirect('contact')
    
    return render(request, 'contact.html')

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
    """Handle Stripe webhooks"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    
    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        logger.info(f"Payment succeeded: {payment_intent['id']}")
    
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        logger.error(f"Payment failed: {payment_intent['id']}")
    
    return HttpResponse(status=200)