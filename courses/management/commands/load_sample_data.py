from django.core.management.base import BaseCommand
from django.core.management import call_command
from courses.models import Course, Instructor
from datetime import date

class Command(BaseCommand):
    help = 'Load sample course data'

    def handle(self, *args, **options):
        # Create the main course
        course, created = Course.objects.get_or_create(
            title="From Powerless to Powerful: Grow Real Change with the Land",
            defaults={
                'subtitle': 'Creating real transformation through hands-on connection with nature',
                'description': '"Creating real change" has of late become a damp squib statement, where the gravitas of words ultimately only serves to prepare us for disappointment. The land isn\'t like that. The land is constantly invoking change, creating new paradigms and realities and teaching us how to live in ways which create and fulfil. In this course, we will listen intently to what the soil and plants can show us about growing colourful, meaningful and powerful change in a world in which that possibility can seem so far away.',
                'what_you_will_experience': 'This course is designed not as a pit-stop knowledge share, but as an ongoing, communal relationship with land and nature. Undertaking tasks with and on real land, you will work with your hands on various substrates and will grow a plethora of plants used for many purposes, from making delicious food to creating effective medicines and clothes.',
                'course_structure': 'A monthly course held over five sessions, giving you time to integrate your learnings and observe the changing seasons.',
                'location': 'A unique dual-location experience. Talks will take place at the established Graceworks Permaculture Project in Evington, and our practical, hands-on work will be at The Laurel, a brand new Community Supported Agriculture (CSA) project. You will be among the first to bring this exciting new land to life.',
                'accessibility': 'Both locations are easily accessible, just a 12-minute drive or a 15-minute bus ride from Leicester city centre.',
                'who_this_is_for': 'This course is for anybody who craves change but feels powerless in their day-to-day lives to make it. It is for those who want to see how learning from and working with the land—at its rawest and at its most flourishing—brings monumental shifts both in your own internal world and in the world around you.',
                'what_you_will_gain': 'You will leave with a deep, embodied understanding of the literal, historical, and philosophical roots of working the land. You will also gain the tried and tested knowledge of what it takes to start a 3-acre Community Supported Agriculture Project from the ground up.',
                'start_date': date(2025, 11, 1),
                'duration': 'Five months',
                'max_participants': 15,
                'price': 200.00,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Course created successfully'))
        else:
            self.stdout.write(self.style.WARNING('Course already exists'))
        
        # Create instructor
        instructor, created = Instructor.objects.get_or_create(
            name="Hannah Watkins",
            defaults={
                'bio': '''Hannah Watkins is what can only be described as besotted with vegetable growing. It is rare that people find their passion in life, but it is evident—through her continual commitment to early rising, her perpetual conversation about sprouts (or whatever vegetable is her "favourite" at the time), and over 2 acres of living, flourishing evidence at Community Harvest Whetstone—that she has found her raison d'être. Those around her, even for a few minutes, will begin to feel that obsession—and it is wonderfully infectious.

You would probably not find out that she has a 1st class bachelors degree and a distinction level MSc in Psychology, or that she was the head of equalities for Leicester City Council, or, indeed, that she started a mental health unit for people with severe brain injuries—because one day, she made a plan to be a vegetable farmer and hasn't looked back since. Her old life has been left in the wake of cultivated soil and rarely shaped aubergines.

It is fair to say that you are in safe, muddy hands with Hannah Watkins and that she will share, without reservation, her love for growing and her knowledge thereof. You will no doubt, like her, undergo a kind of transformation into joyful service of the earth, of people, and of community as you hear what she has to say and see what she has to show.'''
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Instructor created successfully'))
        else:
            self.stdout.write(self.style.WARNING('Instructor already exists'))
            
        # Connect instructor to course
        instructor.courses.add(course)
        
        self.stdout.write(self.style.SUCCESS('Sample data loaded successfully!'))
        
        # Now set up pricing tiers
        self.stdout.write('Setting up pricing tiers...')
        try:
            call_command('setup_pricing')
            self.stdout.write(self.style.SUCCESS('Pricing setup completed!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error setting up pricing: {e}'))