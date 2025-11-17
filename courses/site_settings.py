from django.db import models
from django.core.validators import EmailValidator

class SiteSettings(models.Model):
    """
    Global site settings that can be configured through the admin panel.
    This is a singleton model - only one instance should exist.
    """

    # Email settings
    booking_notification_emails = models.TextField(
        default='hannah@hortuscognitor.co.uk',
        help_text='Email addresses to notify when a booking is made. Separate multiple emails with commas.',
        validators=[],
        verbose_name='Booking Notification Emails'
    )

    # Automated Email Reminder Settings

    # Payment Reminders
    payment_reminder_enabled = models.BooleanField(
        default=True,
        verbose_name='Enable Payment Reminders',
        help_text='Send automated payment reminders to customers who paid a deposit and need to pay the final amount.'
    )
    payment_reminder_days_before_list = models.CharField(
        max_length=100,
        default='7,3,1',
        verbose_name='Payment Reminder Days Before',
        help_text='Comma-separated list of days before final payment deadline to send reminders. For example: "7,3,1" sends reminders 7 days before, 3 days before, and 1 day before the deadline.'
    )

    # Course Details Reminders
    course_details_enabled = models.BooleanField(
        default=True,
        verbose_name='Enable Course Details Reminders',
        help_text='Send course details and preparation information to confirmed participants before the course starts.'
    )
    course_details_days_before = models.IntegerField(
        default=7,
        verbose_name='Course Details Days Before',
        help_text='How many days before course start date to send the course details email.'
    )

    # Session Reminders
    session_reminder_enabled = models.BooleanField(
        default=True,
        verbose_name='Enable Session Reminders',
        help_text='Send reminders before individual course sessions.'
    )
    session_reminder_days_before = models.IntegerField(
        default=1,
        verbose_name='Session Reminder Days Before',
        help_text='How many days before each session to send the reminder.'
    )
    session_reminder_per_course = models.CharField(
        max_length=20,
        choices=[
            ('first_only', 'First Session Only'),
            ('all_sessions', 'All Sessions'),
        ],
        default='first_only',
        verbose_name='Session Reminder Frequency',
        help_text='Send reminders only for the first session or for all sessions.'
    )

    # Test Mode Settings
    reminder_test_mode = models.BooleanField(
        default=False,
        verbose_name='Enable Test Mode',
        help_text='When enabled, all automated reminder emails will be sent to the test email address instead of actual recipients. Use this to test the system before going live.'
    )
    reminder_test_email = models.EmailField(
        blank=True,
        default='hannah@hortuscognitor.co.uk',
        verbose_name='Test Email Address',
        help_text='Email address to receive all reminder emails when test mode is enabled.'
    )

    # Singleton enforcement
    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def save(self, *args, **kwargs):
        """Ensure only one instance exists"""
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion of settings"""
        pass

    @classmethod
    def load(cls):
        """Load the singleton instance, creating it if it doesn't exist"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def get_notification_emails(self):
        """Return list of notification email addresses"""
        emails = [email.strip() for email in self.booking_notification_emails.split(',')]
        return [email for email in emails if email]  # Remove empty strings

    def get_payment_reminder_days_list(self):
        """Return list of integers representing days before payment deadline to send reminders"""
        try:
            days_str = self.payment_reminder_days_before_list.strip()
            if not days_str:
                return [7]  # Default to 7 days if empty

            days_list = [int(day.strip()) for day in days_str.split(',') if day.strip()]
            # Remove duplicates and sort in descending order
            return sorted(list(set(days_list)), reverse=True)
        except (ValueError, AttributeError):
            return [7]  # Default to 7 days if parsing fails

    def __str__(self):
        return "Site Settings"
