"""
Management command to send payment reminder emails.
Sends reminders to customers who paid a deposit and need to pay the final amount.
"""
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from datetime import timedelta
from courses.models import CoursePayment, EmailReminder
from courses.site_settings import SiteSettings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send payment reminder emails for unpaid final payments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what emails would be sent without actually sending them',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Send reminders even if they were already sent before (useful for testing)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        self.stdout.write(self.style.MIGRATE_HEADING('\n=== PAYMENT REMINDER PROCESSOR ===\n'))

        # Load site settings
        site_settings = SiteSettings.load()

        # Check if payment reminders are enabled
        if not site_settings.payment_reminder_enabled:
            self.stdout.write(self.style.WARNING('Payment reminders are disabled in Site Settings.'))
            self.stdout.write('Enable them in the Django admin to send payment reminders.')
            return

        # Get configuration
        days_before_list = site_settings.get_payment_reminder_days_list()
        test_mode = site_settings.reminder_test_mode
        test_email = site_settings.reminder_test_email

        if test_mode:
            self.stdout.write(self.style.WARNING(f'⚠️  TEST MODE ENABLED - All emails will be sent to: {test_email}'))

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No emails will actually be sent\n'))

        self.stdout.write(f'Reminder schedule (days before deadline): {days_before_list}\n')

        # Get all payments with unpaid final amounts
        pending_payments = CoursePayment.objects.filter(
            deposit_paid_at__isnull=False,  # Deposit was paid
            final_paid_at__isnull=True,  # Final payment not yet paid
            payment_plan__isnull=False  # Has a payment plan
        ).select_related('booking', 'booking__course', 'payment_plan')

        if not pending_payments.exists():
            self.stdout.write(self.style.SUCCESS('✓ No pending final payments found'))
            return

        self.stdout.write(f'Found {pending_payments.count()} pending final payment(s)\n')

        today = timezone.now().date()
        sent_count = 0
        skipped_count = 0
        error_count = 0

        for payment in pending_payments:
            booking = payment.booking
            course = booking.course
            payment_plan = payment.payment_plan
            final_due_date = payment_plan.final_payment_deadline

            if not final_due_date:
                self.stdout.write(f'⊘ Skipping booking #{booking.id} - No final payment due date set')
                skipped_count += 1
                continue

            # Calculate days until payment due
            days_until_due = (final_due_date - today).days

            # Check if we should send a reminder today
            should_send = days_until_due in days_before_list

            if not should_send:
                continue  # Not a reminder day for this payment

            # Check if reminder already sent for this iteration (unless force flag is set)
            if not force:
                existing_reminder = EmailReminder.objects.filter(
                    course_payment=payment,
                    reminder_type='payment_reminder',
                    days_before_sent=days_until_due
                ).first()

                if existing_reminder:
                    self.stdout.write(
                        f'⊘ Booking #{booking.id} ({booking.email}) - '
                        f'{days_until_due}-day reminder already sent on {existing_reminder.sent_at.strftime("%Y-%m-%d %H:%M")}'
                    )
                    skipped_count += 1
                    continue

            # Determine recipient email (test mode or actual)
            recipient_email = test_email if test_mode else booking.email

            # Generate payment URL
            payment_url = f"{settings.SITE_URL}{reverse('course_payment', kwargs={'slug': course.slug})}"

            # Prepare email context
            context = {
                'booking': booking,
                'course': course,
                'payment': payment,
                'payment_url': payment_url,
            }

            self.stdout.write(self.style.MIGRATE_LABEL(
                f'\n--- {days_until_due} days before deadline ---'
            ))
            self.stdout.write(f'Booking #{booking.id}: {course.title}')
            self.stdout.write(f'Customer: {booking.full_name} ({booking.email})')
            self.stdout.write(f'Deposit: £{payment.deposit_amount} (paid {payment.deposit_paid_at.strftime("%Y-%m-%d")})')
            self.stdout.write(f'Final amount: £{payment.final_amount}')
            self.stdout.write(f'Due date: {final_due_date.strftime("%A, %d %B %Y")}')

            try:
                if not dry_run:
                    # Render email templates
                    html_content = render_to_string('emails/payment_reminder.html', context)
                    text_content = render_to_string('emails/payment_reminder.txt', context)

                    # Create and send email
                    subject = f'Payment Reminder - {course.title}'
                    from_email = settings.DEFAULT_FROM_EMAIL

                    email = EmailMultiAlternatives(
                        subject=subject,
                        body=text_content,
                        from_email=from_email,
                        to=[recipient_email],
                    )
                    email.attach_alternative(html_content, "text/html")
                    email.send(fail_silently=False)

                    # Record successful send
                    EmailReminder.objects.create(
                        course_payment=payment,
                        reminder_type='payment_reminder',
                        days_before_sent=days_until_due,
                        recipient_email=recipient_email,
                        successful=True
                    )

                    test_indicator = ' (TEST MODE)' if test_mode else ''
                    self.stdout.write(f'✓ Sent to: {recipient_email}{test_indicator}')
                    sent_count += 1
                    logger.info(f'Payment reminder sent to {recipient_email} for booking #{booking.id}')

                else:
                    # Dry run - just show what would be sent
                    test_indicator = ' (TEST MODE)' if test_mode else ''
                    self.stdout.write(f'✓ Would send to: {recipient_email}{test_indicator}')
                    sent_count += 1

            except Exception as e:
                error_msg = str(e)
                self.stdout.write(self.style.ERROR(f'✗ Error sending to {recipient_email}: {error_msg}'))
                error_count += 1
                logger.error(f'Error sending payment reminder to {recipient_email}: {error_msg}')

                if not dry_run:
                    # Record failed send
                    EmailReminder.objects.create(
                        course_payment=payment,
                        reminder_type='payment_reminder',
                        days_before_sent=days_until_due,
                        recipient_email=recipient_email,
                        successful=False,
                        error_message=error_msg
                    )

        # Summary
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== SUMMARY ==='))
        action = 'Would send' if dry_run else 'Sent'
        self.stdout.write(f'{action}: {sent_count}')
        self.stdout.write(f'Skipped: {skipped_count}')
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))
        else:
            self.stdout.write(f'Errors: {error_count}')

        if sent_count > 0 and not dry_run:
            self.stdout.write(self.style.SUCCESS(f'\n✓ Payment reminders sent successfully!\n'))
        elif sent_count > 0 and dry_run:
            self.stdout.write(self.style.SUCCESS(f'\n✓ Dry run complete - {sent_count} email(s) would be sent\n'))
        else:
            self.stdout.write('\nNo emails sent.\n')
