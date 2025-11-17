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

    def __str__(self):
        return "Site Settings"
