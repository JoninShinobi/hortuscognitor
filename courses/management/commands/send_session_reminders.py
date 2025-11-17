"""
Management command to send session reminder emails.
Automatically detects upcoming sessions and sends reminders based on SiteSettings configuration.
"""
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from courses.models import CourseSession, Booking, EmailReminder
from courses.site_settings import SiteSettings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send session reminder emails for upcoming course sessions'

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

        self.stdout.write(self.style.MIGRATE_HEADING('\n=== SESSION REMINDER PROCESSOR ===\n'))

        # Load site settings
        site_settings = SiteSettings.load()

        # Check if session reminders are enabled
        if not site_settings.session_reminder_enabled:
            self.stdout.write(self.style.WARNING('Session reminders are disabled in Site Settings.'))
            self.stdout.write('Enable them in the Django admin to send session reminders.')
            return

        # Get configuration
        days_before = site_settings.session_reminder_days_before
        reminder_frequency = site_settings.session_reminder_per_course  # 'first_only' or 'all_sessions'
        test_mode = site_settings.reminder_test_mode
        test_email = site_settings.reminder_test_email

        if test_mode:
            self.stdout.write(self.style.WARNING(f'⚠️  TEST MODE ENABLED - All emails will be sent to: {test_email}'))

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No emails will actually be sent\n'))

        # Calculate target date
        today = timezone.now().date()
        target_date = today + timedelta(days=days_before)

        self.stdout.write(f'Looking for sessions on: {target_date.strftime("%A, %d %B %Y")}')
        self.stdout.write(f'Reminder frequency: {reminder_frequency}\n')

        # Get upcoming sessions on target date
        upcoming_sessions = CourseSession.objects.filter(
            date=target_date
        ).select_related('course').order_by('date', 'start_time')

        if not upcoming_sessions.exists():
            self.stdout.write(self.style.SUCCESS(f'✓ No sessions found for {target_date}'))
            return

        self.stdout.write(f'Found {upcoming_sessions.count()} session(s) on {target_date}\n')

        sent_count = 0
        skipped_count = 0
        error_count = 0

        for session in upcoming_sessions:
            course = session.course

            # Check if this is the first session
            first_session = course.sessions.order_by('date', 'start_time').first()
            is_first_session = (first_session.id == session.id)

            # Apply frequency filter
            if reminder_frequency == 'first_only' and not is_first_session:
                self.stdout.write(f'⊘ Skipping session #{session.session_number} for "{course.title}" (not first session)')
                skipped_count += 1
                continue

            # Get all confirmed bookings for this course (excludes pending and cancelled)
            confirmed_bookings = Booking.objects.filter(
                course=course,
                status='confirmed'
            ).select_related('course')

            if not confirmed_bookings.exists():
                self.stdout.write(f'⊘ No confirmed bookings for "{course.title}" session #{session.session_number}')
                skipped_count += 1
                continue

            self.stdout.write(self.style.MIGRATE_LABEL(
                f'\n--- Session #{session.session_number} for "{course.title}" ---'
            ))
            self.stdout.write(f'Date: {session.date.strftime("%A, %d %B %Y")}')
            self.stdout.write(f'Time: {session.start_time.strftime("%H:%M")} - {session.end_time.strftime("%H:%M")}')
            self.stdout.write(f'Confirmed bookings: {confirmed_bookings.count()}\n')

            for booking in confirmed_bookings:
                # Check if reminder already sent (unless force flag is set)
                if not force:
                    existing_reminder = EmailReminder.objects.filter(
                        course_session=session,
                        reminder_type='session_reminder',
                        recipient_email=booking.email,
                        days_before_sent=days_before
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
                    'session': session,
                    'is_first_session': is_first_session
                }

                try:
                    if not dry_run:
                        # Render email templates
                        html_content = render_to_string('emails/session_reminder.html', context)
                        text_content = render_to_string('emails/session_reminder.txt', context)

                        # Create and send email
                        subject = f'Session Reminder - {course.title}'
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
                            course_session=session,
                            reminder_type='session_reminder',
                            days_before_sent=days_before,
                            recipient_email=recipient_email,
                            successful=True
                        )

                        test_indicator = ' (TEST MODE)' if test_mode else ''
                        self.stdout.write(f'  ✓ {recipient_email}{test_indicator}')
                        sent_count += 1
                        logger.info(f'Session reminder sent to {recipient_email} for session #{session.session_number}')

                    else:
                        # Dry run - just show what would be sent
                        test_indicator = ' (TEST MODE)' if test_mode else ''
                        self.stdout.write(f'  ✓ Would send to: {recipient_email}{test_indicator}')
                        sent_count += 1

                except Exception as e:
                    error_msg = str(e)
                    self.stdout.write(self.style.ERROR(f'  ✗ {recipient_email} - Error: {error_msg}'))
                    error_count += 1
                    logger.error(f'Error sending session reminder to {recipient_email}: {error_msg}')

                    if not dry_run:
                        # Record failed send
                        EmailReminder.objects.create(
                            course_session=session,
                            reminder_type='session_reminder',
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
            self.stdout.write(self.style.SUCCESS(f'\n✓ Session reminders sent successfully!\n'))
        elif sent_count > 0 and dry_run:
            self.stdout.write(self.style.SUCCESS(f'\n✓ Dry run complete - {sent_count} email(s) would be sent\n'))
        else:
            self.stdout.write('\nNo emails sent.\n')
