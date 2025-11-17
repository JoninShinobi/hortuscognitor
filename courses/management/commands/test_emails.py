from django.core.management.base import BaseCommand
from django.utils import timezone
from courses.models import Course, Booking, PricingTier, PaymentPlan, CoursePayment
from courses.views import send_course_confirmation_email, send_admin_booking_notification


class Command(BaseCommand):
    help = 'Send test emails to verify email configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send test to (default: hannah@hortuscognitor.co.uk)',
            default='hannah@hortuscognitor.co.uk'
        )

    def handle(self, *args, **options):
        test_email = options['email']
        
        try:
            # Get the first active course
            course = Course.objects.filter(is_active=True).first()
            if not course:
                self.stdout.write(self.style.ERROR('No active courses found'))
                return
            
            # Get pricing tier
            pricing_tier = course.pricing_tiers.first()
            if not pricing_tier:
                self.stdout.write(self.style.ERROR('No pricing tiers found for course'))
                return
            
            # Get payment plan
            payment_plan = PaymentPlan.objects.filter(is_active=True).first()
            if not payment_plan:
                self.stdout.write(self.style.ERROR('No active payment plans found'))
                return
            
            # Create a test booking
            booking = Booking.objects.create(
                course=course,
                full_name='Test User',
                email=test_email,
                phone='07123456789',
                message='This is a test booking - please ignore',
            )
            
            # Create a test payment
            course_payment = CoursePayment.objects.create(
                booking=booking,
                pricing_tier=pricing_tier,
                payment_plan=payment_plan,
                status='fully_paid',
                deposit_paid_at=timezone.now(),
                final_paid_at=timezone.now(),
            )
            
            self.stdout.write(self.style.SUCCESS(f'Created test booking #{booking.id}'))
            
            # Send emails
            self.stdout.write('Sending customer confirmation email...')
            send_course_confirmation_email(course_payment)
            self.stdout.write(self.style.SUCCESS(f'✓ Customer email sent to {test_email}'))
            
            self.stdout.write('Sending admin notification email...')
            send_admin_booking_notification(course_payment)
            self.stdout.write(self.style.SUCCESS('✓ Admin notification email sent'))
            
            self.stdout.write(self.style.SUCCESS(f'\nTest emails sent successfully!'))
            self.stdout.write(f'Test booking ID: {booking.id}')
            self.stdout.write(f'You can delete this test booking from the admin panel.')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error sending test emails: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
