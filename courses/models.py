from django.db import models
from django.utils.text import slugify
from django.core.validators import RegexValidator, MinLengthValidator, MaxLengthValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import re

class Course(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    hero_image = models.ImageField(upload_to='courses/hero_images/', blank=True, null=True, help_text='Recommended size: 1920x1080px (16:9 aspect ratio)')
    description = models.TextField(blank=True)
    what_you_will_experience = models.TextField(blank=True)
    course_structure = models.TextField(blank=True)
    location = models.TextField(blank=True)
    accessibility = models.TextField(blank=True)
    who_this_is_for = models.TextField(blank=True)
    what_you_will_gain = models.TextField(blank=True)
    start_date = models.DateField()
    duration = models.CharField(max_length=100)
    max_participants = models.IntegerField(default=15)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    slug = models.SlugField(unique=True, max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title

    @property
    def confirmed_bookings_count(self):
        """Count bookings with confirmed payments (deposit_paid or fully_paid)"""
        return self.bookings.filter(
            payment__status__in=['deposit_paid', 'fully_paid']
        ).count()

    @property
    def spaces_left(self):
        """Calculate remaining spaces based on max participants and confirmed bookings"""
        return self.max_participants - self.confirmed_bookings_count

    class Meta:
        ordering = ['start_date']

class CourseSession(models.Model):
    """Individual session dates and times for a course"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sessions')
    session_number = models.IntegerField(help_text='Session number (e.g., 1, 2, 3)')
    date = models.DateField(help_text='Date of this session')
    start_time = models.TimeField(help_text='Start time of this session')
    end_time = models.TimeField(help_text='End time of this session')

    class Meta:
        ordering = ['session_number']
        unique_together = ['course', 'session_number']

    def __str__(self):
        return f"{self.course.title} - Session {self.session_number}: {self.date.strftime('%d %B %Y')} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"

class Instructor(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField()
    photo = models.ImageField(upload_to='instructors/', blank=True, null=True)
    courses = models.ManyToManyField(Course, related_name='instructors')

    def __str__(self):
        return self.name

def validate_no_html(value):
    """Validator to prevent HTML/script injection"""
    if re.search(r'<[^>]*>', value):
        raise ValidationError('HTML tags are not allowed.')
    
    dangerous_patterns = [
        r'javascript:', r'onclick=', r'onerror=', r'onload=',
        r'eval\(', r'document\.', r'window\.'
    ]
    
    value_lower = value.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, value_lower):
            raise ValidationError('Potentially unsafe content detected.')

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)
    full_name = models.CharField(
        max_length=100,
        validators=[
            MinLengthValidator(2, "Name must be at least 2 characters long."),
            RegexValidator(
                regex=r'^[A-Za-z\s\-\.\''']+$',
                message='Name can only contain letters, spaces, hyphens, periods, and apostrophes.'
            ),
            validate_no_html
        ],
        help_text="Full name (2-100 characters, letters only)"
    )
    email = models.EmailField(
        max_length=254,
        validators=[validate_no_html],
        help_text="Valid email address"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^[0-9\s\+\-\(\)]*$',
                message='Phone number can only contain numbers, spaces, +, -, (, and ).'
            ),
            validate_no_html
        ],
        help_text="Optional phone number"
    )
    message = models.TextField(
        blank=True,
        max_length=1000,
        validators=[validate_no_html],
        help_text="Optional message (maximum 1000 characters)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Booking status - set to 'confirmed' once payment received, 'cancelled' to stop reminders"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def clean(self):
        """Additional model-level validation"""
        super().clean()
        
        # Validate phone number has sufficient digits if provided
        if self.phone:
            digits_only = re.sub(r'[^0-9]', '', self.phone)
            if len(digits_only) < 6:
                raise ValidationError({'phone': 'Phone number must contain at least 6 digits.'})
            if len(digits_only) > 15:
                raise ValidationError({'phone': 'Phone number must contain no more than 15 digits.'})
    
    def save(self, *args, **kwargs):
        """Override save to run full_clean validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        if self.course:
            return f"{self.full_name} - {self.course.title}"
        else:
            return f"{self.full_name} - Contact Form"
    
    class Meta:
        ordering = ['-created_at']


class PricingTier(models.Model):
    """Three-tier pricing structure for courses"""
    TIER_CHOICES = [
        ('basic', 'Basic Tier - Meeting Basic Needs'),
        ('standard', 'Standard Tier - Regular Income'),
        ('solidarity', 'Solidarity Tier - Financially Secure'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='pricing_tiers')
    tier = models.CharField(max_length=20, choices=TIER_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sessions = models.IntegerField(default=5)
    description = models.TextField()
    
    class Meta:
        unique_together = ['course', 'tier']
        ordering = ['price']
    
    def __str__(self):
        return f"{self.course.title} - {self.get_tier_display()} - £{self.price}"
    
    @property
    def price_per_session(self):
        return self.price / self.sessions if self.sessions > 0 else 0


class PaymentPlan(models.Model):
    """Payment plan options: full payment or installments"""
    PLAN_CHOICES = [
        ('full', 'Pay in Full'),
        ('installment', 'Pay in Two Installments'),
    ]
    
    name = models.CharField(max_length=20, choices=PLAN_CHOICES)
    deposit_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # 0 for full, 50 for installment
    deposit_deadline = models.DateField()
    final_payment_deadline = models.DateField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.get_name_display()


class CoursePayment(models.Model):
    """Main payment tracking for course bookings"""
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('deposit_paid', 'Deposit Paid'),
        ('fully_paid', 'Fully Paid'),
        ('overdue', 'Payment Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    pricing_tier = models.ForeignKey(PricingTier, on_delete=models.CASCADE)
    payment_plan = models.ForeignKey(PaymentPlan, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Stripe integration
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Payment amounts
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment tracking
    deposit_paid_at = models.DateTimeField(null=True, blank=True)
    final_paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Calculate amounts based on pricing tier and payment plan
        self.total_amount = self.pricing_tier.price
        if self.payment_plan.name == 'installment':
            self.deposit_amount = self.total_amount * (self.payment_plan.deposit_percentage / 100)
            self.final_amount = self.total_amount - self.deposit_amount
        else:
            self.deposit_amount = self.total_amount
            self.final_amount = Decimal('0.00')
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Payment for {self.booking.full_name} - {self.pricing_tier.course.title}"
    
    @property
    def is_overdue(self):
        now = timezone.now().date()
        if self.status == 'pending' and self.payment_plan.deposit_deadline < now:
            return True
        if self.status == 'deposit_paid' and self.payment_plan.final_payment_deadline < now:
            return True
        return False
    
    @property
    def next_payment_due(self):
        if self.status == 'pending':
            return self.deposit_amount
        elif self.status == 'deposit_paid':
            return self.final_amount
        return Decimal('0.00')


class StripePaymentRecord(models.Model):
    """Track individual Stripe payment transactions"""
    PAYMENT_TYPE_CHOICES = [
        ('deposit', 'Deposit Payment'),
        ('full', 'Full Payment'),
        ('final', 'Final Payment'),
    ]
    
    course_payment = models.ForeignKey(CoursePayment, on_delete=models.CASCADE, related_name='stripe_payments')
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE_CHOICES)
    stripe_payment_intent_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='gbp')
    status = models.CharField(max_length=20)  # succeeded, pending, failed, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_payment_type_display()} - £{self.amount} - {self.status}"


class EmailReminder(models.Model):
    """Track automated reminder emails sent to prevent duplicates and for monitoring"""
    REMINDER_TYPE_CHOICES = [
        ('payment_reminder', 'Payment Reminder'),
        ('course_details', 'Course Details'),
        ('session_reminder', 'Session Reminder'),
    ]

    # Foreign keys (nullable to support different reminder types)
    course_payment = models.ForeignKey(
        CoursePayment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='email_reminders',
        help_text='Related course payment (for payment reminders)'
    )
    course_session = models.ForeignKey(
        CourseSession,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='email_reminders',
        help_text='Related course session (for session reminders)'
    )

    # Reminder details
    reminder_type = models.CharField(
        max_length=20,
        choices=REMINDER_TYPE_CHOICES,
        help_text='Type of reminder email sent'
    )
    days_before_sent = models.IntegerField(
        null=True,
        blank=True,
        help_text='How many days before the event this reminder was sent (e.g., 7 for "7 days before")'
    )

    # Email tracking
    recipient_email = models.EmailField(help_text='Email address the reminder was sent to')
    sent_at = models.DateTimeField(auto_now_add=True, help_text='When the reminder was sent')
    successful = models.BooleanField(
        default=True,
        help_text='Whether the email was sent successfully'
    )
    error_message = models.TextField(
        blank=True,
        help_text='Error message if email failed to send'
    )

    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Email Reminder'
        verbose_name_plural = 'Email Reminders'
        indexes = [
            models.Index(fields=['reminder_type', 'sent_at']),
            models.Index(fields=['course_payment', 'reminder_type', 'days_before_sent']),
            models.Index(fields=['course_session', 'reminder_type']),
        ]

    def __str__(self):
        status = "✓" if self.successful else "✗"
        days_info = f" ({self.days_before_sent} days before)" if self.days_before_sent else ""
        return f"{status} {self.get_reminder_type_display()}{days_info} to {self.recipient_email} at {self.sent_at.strftime('%Y-%m-%d %H:%M')}"


# Import site settings at the end to avoid circular import
from .site_settings import SiteSettings