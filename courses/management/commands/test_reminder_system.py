"""
Management command to test the reminder system configuration and setup.
Tests models, templates, and configuration without sending actual emails.
"""
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from courses.models import (
    Course, CourseSession, Booking, PricingTier, PaymentPlan,
    CoursePayment, EmailReminder, SiteSettings
)
from courses.site_settings import SiteSettings as SiteSettingsModel


class Command(BaseCommand):
    help = 'Test the reminder system setup and configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each test',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']

        self.stdout.write(self.style.MIGRATE_HEADING('\n=== REMINDER SYSTEM TEST SUITE ===\n'))

        passed = 0
        failed = 0

        # Test 1: SiteSettings Model
        test_name = "SiteSettings Model Configuration"
        try:
            settings = SiteSettings.load()

            # Check all new fields exist
            required_fields = [
                'payment_reminder_enabled',
                'payment_reminder_days_before_list',
                'course_details_enabled',
                'course_details_days_before',
                'session_reminder_enabled',
                'session_reminder_days_before',
                'session_reminder_per_course',
                'reminder_test_mode',
                'reminder_test_email',
            ]

            for field in required_fields:
                assert hasattr(settings, field), f"Missing field: {field}"

            # Check default values
            assert settings.payment_reminder_days_before_list == '7,3,1', "Incorrect default for payment_reminder_days_before_list"
            assert settings.course_details_days_before == 7, "Incorrect default for course_details_days_before"
            assert settings.session_reminder_days_before == 1, "Incorrect default for session_reminder_days_before"
            assert settings.session_reminder_per_course == 'first_only', "Incorrect default for session_reminder_per_course"

            if verbose:
                self.stdout.write(f"  ✓ All {len(required_fields)} reminder fields exist")
                self.stdout.write(f"  ✓ Default values correct")

            self.stdout.write(self.style.SUCCESS(f'✓ {test_name}'))
            passed += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ {test_name}: {str(e)}'))
            failed += 1

        # Test 2: Payment Reminder Days Parser
        test_name = "Payment Reminder Days Parser"
        try:
            settings = SiteSettings.load()

            # Test default parsing
            days = settings.get_payment_reminder_days_list()
            assert days == [7, 3, 1], f"Expected [7, 3, 1], got {days}"

            # Test custom parsing
            settings.payment_reminder_days_before_list = '14,7,3'
            days = settings.get_payment_reminder_days_list()
            assert days == [14, 7, 3], f"Expected [14, 7, 3], got {days}"

            # Test with spaces
            settings.payment_reminder_days_before_list = ' 10 , 5 , 2 '
            days = settings.get_payment_reminder_days_list()
            assert days == [10, 5, 2], f"Expected [10, 5, 2], got {days}"

            # Test deduplication
            settings.payment_reminder_days_before_list = '7,7,3,3,1'
            days = settings.get_payment_reminder_days_list()
            assert days == [7, 3, 1], f"Expected deduplicated [7, 3, 1], got {days}"

            # Reset to default
            settings.payment_reminder_days_before_list = '7,3,1'
            settings.save()

            if verbose:
                self.stdout.write(f"  ✓ Default parsing: [7, 3, 1]")
                self.stdout.write(f"  ✓ Custom parsing: [14, 7, 3]")
                self.stdout.write(f"  ✓ Whitespace handling")
                self.stdout.write(f"  ✓ Deduplication")

            self.stdout.write(self.style.SUCCESS(f'✓ {test_name}'))
            passed += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ {test_name}: {str(e)}'))
            failed += 1

        # Test 3: EmailReminder Model
        test_name = "EmailReminder Model"
        try:
            # Check model exists and has correct fields
            reminder_fields = [
                'course_payment',
                'course_session',
                'reminder_type',
                'days_before_sent',
                'recipient_email',
                'sent_at',
                'successful',
                'error_message',
            ]

            for field in reminder_fields:
                assert hasattr(EmailReminder, field), f"Missing field: {field}"

            # Check choices
            reminder_types = [choice[0] for choice in EmailReminder.REMINDER_TYPE_CHOICES]
            expected_types = ['payment_reminder', 'course_details', 'session_reminder']
            assert set(reminder_types) == set(expected_types), f"Incorrect reminder types"

            if verbose:
                self.stdout.write(f"  ✓ All {len(reminder_fields)} fields exist")
                self.stdout.write(f"  ✓ Reminder type choices: {', '.join(expected_types)}")

            self.stdout.write(self.style.SUCCESS(f'✓ {test_name}'))
            passed += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ {test_name}: {str(e)}'))
            failed += 1

        # Test 4: EmailReminder Creation
        test_name = "EmailReminder Record Creation"
        try:
            # Create a test reminder
            test_reminder = EmailReminder.objects.create(
                reminder_type='session_reminder',
                days_before_sent=1,
                recipient_email='test@example.com',
                successful=True
            )

            # Verify it was created
            assert test_reminder.pk is not None, "Reminder not saved to database"
            assert test_reminder.reminder_type == 'session_reminder'
            assert test_reminder.recipient_email == 'test@example.com'
            assert test_reminder.successful == True

            # Check __str__ method
            str_repr = str(test_reminder)
            assert '✓' in str_repr, "Success emoji not in string representation"
            assert 'Session Reminder' in str_repr, "Reminder type not in string representation"

            # Clean up
            test_reminder.delete()

            if verbose:
                self.stdout.write(f"  ✓ Record created successfully")
                self.stdout.write(f"  ✓ __str__ method: {str_repr[:50]}...")

            self.stdout.write(self.style.SUCCESS(f'✓ {test_name}'))
            passed += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ {test_name}: {str(e)}'))
            failed += 1

        # Test 5: Session Reminder Template (HTML)
        test_name = "Session Reminder Template (HTML)"
        try:
            # Create mock context
            now = timezone.now()
            context = {
                'booking': type('obj', (object,), {
                    'full_name': 'Test User',
                    'email': 'test@example.com'
                }),
                'course': type('obj', (object,), {
                    'title': 'Test Course',
                    'location': 'Test Location'
                }),
                'session': type('obj', (object,), {
                    'session_number': 1,
                    'date': now.date(),
                    'start_time': now.time(),
                    'end_time': (now + timedelta(hours=2)).time()
                }),
                'is_first_session': True
            }

            # Render template
            html_content = render_to_string('emails/session_reminder.html', context)

            # Check required elements are present
            assert 'Session Reminder' in html_content, "Missing title"
            assert 'Test User' in html_content, "Missing recipient name"
            assert 'Test Course' in html_content, "Missing course title"
            assert 'Session 1' in html_content, "Missing session number"
            assert 'What to Bring' in html_content, "Missing first session section"
            assert 'Hannah' in html_content, "Missing signature"
            assert '#ADA228' in html_content, "Missing brand color"
            assert 'hortuscognitor.co.uk' in html_content, "Missing website link"

            if verbose:
                self.stdout.write(f"  ✓ Template renders successfully")
                self.stdout.write(f"  ✓ All required elements present")
                self.stdout.write(f"  ✓ First session section conditional works")

            self.stdout.write(self.style.SUCCESS(f'✓ {test_name}'))
            passed += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ {test_name}: {str(e)}'))
            failed += 1

        # Test 6: Session Reminder Template (TXT)
        test_name = "Session Reminder Template (TXT)"
        try:
            # Use same context as HTML test
            now = timezone.now()
            context = {
                'booking': type('obj', (object,), {
                    'full_name': 'Test User',
                    'email': 'test@example.com'
                }),
                'course': type('obj', (object,), {
                    'title': 'Test Course',
                    'location': 'Test Location'
                }),
                'session': type('obj', (object,), {
                    'session_number': 1,
                    'date': now.date(),
                    'start_time': now.time(),
                    'end_time': (now + timedelta(hours=2)).time()
                }),
                'is_first_session': True
            }

            # Render template
            txt_content = render_to_string('emails/session_reminder.txt', context)

            # Check required elements
            assert 'HORTUS COGNITOR' in txt_content, "Missing header"
            assert 'Session Reminder' in txt_content, "Missing title"
            assert 'Test User' in txt_content, "Missing recipient name"
            assert 'Test Course' in txt_content, "Missing course title"
            assert 'WHAT TO BRING' in txt_content, "Missing first session section"
            assert 'Hannah' in txt_content, "Missing signature"

            if verbose:
                self.stdout.write(f"  ✓ Template renders successfully")
                self.stdout.write(f"  ✓ All required elements present")

            self.stdout.write(self.style.SUCCESS(f'✓ {test_name}'))
            passed += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ {test_name}: {str(e)}'))
            failed += 1

        # Test 7: Non-first Session Template Rendering
        test_name = "Session Template (Non-first Session)"
        try:
            now = timezone.now()
            context = {
                'booking': type('obj', (object,), {
                    'full_name': 'Test User',
                    'email': 'test@example.com'
                }),
                'course': type('obj', (object,), {
                    'title': 'Test Course',
                    'location': 'Test Location'
                }),
                'session': type('obj', (object,), {
                    'session_number': 3,
                    'date': now.date(),
                    'start_time': now.time(),
                    'end_time': (now + timedelta(hours=2)).time()
                }),
                'is_first_session': False
            }

            html_content = render_to_string('emails/session_reminder.html', context)
            txt_content = render_to_string('emails/session_reminder.txt', context)

            # Should NOT include "What to Bring" section
            assert 'What to Bring' not in html_content, "First session section should not appear"
            assert 'WHAT TO BRING' not in txt_content, "First session section should not appear in TXT"

            # Should still include session number
            assert 'Session 3' in html_content, "Missing session number"

            if verbose:
                self.stdout.write(f"  ✓ First session section correctly hidden")
                self.stdout.write(f"  ✓ Session number displays correctly")

            self.stdout.write(self.style.SUCCESS(f'✓ {test_name}'))
            passed += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ {test_name}: {str(e)}'))
            failed += 1

        # Test 8: Test Mode Configuration
        test_name = "Test Mode Configuration"
        try:
            settings = SiteSettings.load()

            # Test default state
            assert settings.reminder_test_mode == False, "Test mode should be disabled by default"
            assert settings.reminder_test_email == 'hannah@hortuscognitor.co.uk', "Incorrect default test email"

            # Test toggling
            settings.reminder_test_mode = True
            settings.reminder_test_email = 'testing@example.com'
            settings.save()

            # Reload and verify
            settings = SiteSettings.load()
            assert settings.reminder_test_mode == True, "Test mode toggle failed"
            assert settings.reminder_test_email == 'testing@example.com', "Test email update failed"

            # Reset
            settings.reminder_test_mode = False
            settings.reminder_test_email = 'hannah@hortuscognitor.co.uk'
            settings.save()

            if verbose:
                self.stdout.write(f"  ✓ Default state correct")
                self.stdout.write(f"  ✓ Toggle works")
                self.stdout.write(f"  ✓ Settings persist")

            self.stdout.write(self.style.SUCCESS(f'✓ {test_name}'))
            passed += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ {test_name}: {str(e)}'))
            failed += 1

        # Summary
        total = passed + failed
        self.stdout.write(self.style.MIGRATE_HEADING(f'\n=== TEST RESULTS ==='))
        self.stdout.write(f'Total Tests: {total}')
        self.stdout.write(self.style.SUCCESS(f'Passed: {passed}'))
        if failed > 0:
            self.stdout.write(self.style.ERROR(f'Failed: {failed}'))
        else:
            self.stdout.write(f'Failed: {failed}')

        if failed == 0:
            self.stdout.write(self.style.SUCCESS(f'\n✓ All tests passed! Reminder system is ready.\n'))
        else:
            self.stdout.write(self.style.ERROR(f'\n✗ Some tests failed. Please review errors above.\n'))
