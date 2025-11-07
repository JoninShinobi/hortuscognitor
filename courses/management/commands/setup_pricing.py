from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from courses.models import Course, PricingTier, PaymentPlan


class Command(BaseCommand):
    help = 'Set up the three-tier pricing structure and payment plans for Hortus Cognitor courses'

    def handle(self, *args, **options):
        # Create payment plans
        full_payment_plan, created = PaymentPlan.objects.get_or_create(
            name='full',
            defaults={
                'deposit_percentage': 100,
                'deposit_deadline': date(2026, 1, 9),  # 9th Jan 2026
                'final_payment_deadline': date(2026, 1, 9),
                'is_active': True
            }
        )
        
        installment_plan, created = PaymentPlan.objects.get_or_create(
            name='installment',
            defaults={
                'deposit_percentage': 50,
                'deposit_deadline': date(2025, 12, 9),  # 9th Dec 2025
                'final_payment_deadline': date(2026, 1, 9),  # 9th Jan 2026
                'is_active': True
            }
        )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created payment plans')
        )
        
        # Set up pricing tiers for all courses
        courses = Course.objects.all()
        
        for course in courses:
            # Basic tier - £225
            basic_tier, created = PricingTier.objects.get_or_create(
                course=course,
                tier='basic',
                defaults={
                    'price': 225.00,
                    'sessions': 5,
                    'description': """You're meeting your basic needs but things are tight. 
                    You think about money a lot and extra spending - on things like time off, travel, 
                    new clothes, meals out - is rare or never. This tier helps you join without 
                    tipping into financial stress."""
                }
            )
            
            # Standard tier - £325
            standard_tier, created = PricingTier.objects.get_or_create(
                course=course,
                tier='standard',
                defaults={
                    'price': 325.00,
                    'sessions': 5,
                    'description': """You have a regular/steady income and your basic needs are covered, 
                    although you may budget around debt or expenses. You can save occasionally and spend 
                    on non-essentials with some planning. This tier may require some short term tradeoffs, 
                    but it is doable."""
                }
            )
            
            # Solidarity tier - £475
            solidarity_tier, created = PricingTier.objects.get_or_create(
                course=course,
                tier='solidarity',
                defaults={
                    'price': 475.00,
                    'sessions': 5,
                    'description': """You're financially secure. You can meet your needs, cover your wants, 
                    and make investments without too much strain. This tier keeps this work regenerative 
                    by redistributing wealth, to enable access for others."""
                }
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully set up pricing tiers for "{course.title}"')
            )
        
        self.stdout.write(
            self.style.SUCCESS('✅ Pricing structure setup complete!')
        )
        self.stdout.write('')
        self.stdout.write('📊 Pricing Summary:')
        self.stdout.write('• Basic Tier: £225 (£45 per session)')
        self.stdout.write('• Standard Tier: £325 (£65 per session)')
        self.stdout.write('• Solidarity Tier: £475 (£95 per session)')
        self.stdout.write('')
        self.stdout.write('💰 Payment Options:')
        self.stdout.write('• Pay in full by 9th Jan 2026')
        self.stdout.write('• Pay 50% deposit by 9th Dec 2025, remaining 50% by 9th Jan 2026')
        self.stdout.write('')
        self.stdout.write('🎓 Course starts: 17th January 2026')