"""
Management command to send course details reminder emails.
Sends course preparation information to confirmed participants before courses start.
"""
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from courses.models import Course, Booking, EmailReminder
from courses.site_settings import SiteSettings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send course details and preparation emails before courses start'

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

        self.stdout.write(self.style.MIGRATE_HEADING('\n=== COURSE DETAILS REMINDER PROCESSOR ===\n'))

        # Load site settings
        site_settings = SiteSettings.load()

        # Check if course details reminders are enabled
        if not site_settings.course_details_enabled:
            self.stdout.write(self.style.WARNING('Course details reminders are disabled in Site Settings.'))
            self.stdout.write('Enable them in the Django admin to send course details reminders.')
            return

        # Get configuration
        days_before = site_settings.course_details_days_before
        test_mode = site_settings.reminder_test_mode
        test_email = site_settings.reminder_test_email

        if test_mode:
            self.stdout.write(self.style.WARNING(f'⚠️  TEST MODE ENABLED - All emails will be sent to: {test_email}'))

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No emails will actually be sent\n'))

        # Calculate target date
        today = timezone.now().date()
        target_date = today + timedelta(days=days_before)

        self.stdout.write(f'Looking for courses starting on: {target_date.strftime("%A, %d %B %Y")}')
        self.stdout.write(f'Reminder timing: {days_before} days before course start\n')

        # Get courses starting on target date
        starting_courses = Course.objects.filter(
            start_date=target_date,
            is_active=True
        )

        if not starting_courses.exists():
            self.stdout.write(self.style.SUCCESS(f'✓ No courses starting on {target_date}'))
            return

        self.stdout.write(f'Found {starting_courses.count()} course(s) starting on {target_date}\n')

        sent_count = 0
        skipped_count = 0
        error_count = 0

        for course in starting_courses:
            # Get all confirmed bookings for this course (excludes pending and cancelled)
            confirmed_bookings = Booking.objects.filter(
                course=course,
                status='confirmed'
            )

            if not confirmed_bookings.exists():
                self.stdout.write(f'⊘ No confirmed bookings for "{course.title}"')
                skipped_count += 1
                continue

            self.stdout.write(self.style.MIGRATE_LABEL(
                f'\n--- "{course.title}" ---'
            ))
            self.stdout.write(f'Start date: {course.start_date.strftime("%A, %d %B %Y")}')
            if course.end_date:
                self.stdout.write(f'End date: {course.end_date.strftime("%A, %d %B %Y")}')
            self.stdout.write(f'Confirmed bookings: {confirmed_bookings.count()}\n')

            for booking in confirmed_bookings:
                # Check if reminder already sent (unless force flag is set)
                if not force:
                    # For course details, we don't link to a specific session
                    # We link to the course payment to identify which course this reminder is for
                    payment = booking.payments.first()
                    if payment:
                        existing_reminder = EmailReminder.objects.filter(
                            course_payment=payment,
                            reminder_type='course_details',
                            recipient_email=booking.email
                        ).first()

                        if existing_reminder:
                            self.stdout.write(f'  ⊘ {booking.email} - Already sent on {existing_reminder.sent_at.strftime("%Y-%m-%d %H:%M")}')
                            skipped_count += 1
                            continue

                # Determine recipient email (test mode or actual)
                recipient_email = test_email if test_mode else booking.email

                # Prepare email context
                context = {
                    'booking': booking,
                    'course': course,
                }

                try:
                    if not dry_run:
                        # Render email templates
                        html_content = render_to_string('emails/course_details.html', context)
                        text_content = render_to_string('emails/course_details.txt', context)

                        # Create and send email
                        subject = f'Course Details & Preparation - {course.title}'
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
                        # Use course payment as foreign key to track which course this reminder is for
                        payment = booking.payments.first()
                        if payment:
                            EmailReminder.objects.create(
                                course_payment=payment,
                                reminder_type='course_details',
                                days_before_sent=days_before,
                                recipient_email=recipient_email,
                                successful=True
                            )

                        test_indicator = ' (TEST MODE)' if test_mode else ''
                        self.stdout.write(f'  ✓ {recipient_email}{test_indicator}')
                        sent_count += 1
                        logger.info(f'Course details sent to {recipient_email} for {course.title}')

                    else:
                        # Dry run - just show what would be sent
                        test_indicator = ' (TEST MODE)' if test_mode else ''
                        self.stdout.write(f'  ✓ Would send to: {recipient_email}{test_indicator}')
                        sent_count += 1

                except Exception as e:
                    error_msg = str(e)
                    self.stdout.write(self.style.ERROR(f'  ✗ {recipient_email} - Error: {error_msg}'))
                    error_count += 1
                    logger.error(f'Error sending course details to {recipient_email}: {error_msg}')

                    if not dry_run:
                        # Record failed send
                        payment = booking.payments.first()
                        if payment:
                            EmailReminder.objects.create(
                                course_payment=payment,
                                reminder_type='course_details',
                                days_before_sent=days_before,
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
            self.stdout.write(self.style.SUCCESS(f'\n✓ Course details reminders sent successfully!\n'))
        elif sent_count > 0 and dry_run:
            self.stdout.write(self.style.SUCCESS(f'\n✓ Dry run complete - {sent_count} email(s) would be sent\n'))
        else:
            self.stdout.write('\nNo emails sent.\n')
