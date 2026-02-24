from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from admissions.models import Course, Application, SeatAllocation
from django.utils import timezone
from django.db import IntegrityError
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Populate database with sample data for testing'

    def add_arguments(self, parser):
        """Add command line arguments"""
        parser.add_argument(
            '--students',
            type=int,
            default=5,
            help='Number of sample students to create (default: 5)'
        )
        parser.add_argument(
            '--officers',
            type=int,
            default=2,
            help='Number of sample officers to create (default: 2)'
        )
        parser.add_argument(
            '--courses',
            type=int,
            default=8,
            help='Number of sample courses to create (default: 8)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='password123',
            help='Default password for all test users (default: password123)'
        )

    def handle(self, *args, **options):
        """Main command handler"""
        
        # Get options
        num_students = options['students']
        num_officers = options['officers']
        num_courses = options['courses']
        clear_existing = options['clear']
        default_password = options['password']
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('🚀 STARTING SAMPLE DATA POPULATION'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        # Clear existing data if requested
        if clear_existing:
            self.clear_existing_data()
        
        # Create groups
        self.create_groups()
        
        # Create sample courses
        self.create_sample_courses(num_courses)
        
        # Create sample users
        self.create_sample_students(num_students, default_password)
        self.create_sample_officers(num_officers, default_password)
        
        # Create sample applications
        self.create_sample_applications()
        
        # Show summary
        self.show_summary()

    def clear_existing_data(self):
        """Clear all existing sample data"""
        self.stdout.write(self.style.WARNING('\n🗑️  Clearing existing data...'))
        
        SeatAllocation.objects.all().delete()
        Application.objects.all().delete()
        Course.objects.all().delete()
        
        # Don't delete users - they might be needed
        # User.objects.filter(is_superuser=False).delete()
        
        self.stdout.write(self.style.SUCCESS('✓ Existing data cleared'))

    def create_groups(self):
        """Create user groups if they don't exist"""
        self.stdout.write(self.style.SUCCESS('\n📋 Creating user groups...'))
        
        groups = ['Students', 'Admission Officers']
        for group_name in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created group: {group_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠️ Group already exists: {group_name}'))
        
        self.stdout.write(self.style.SUCCESS('✓ Groups setup complete'))

    def create_sample_students(self, count, password):
        """Create sample student users"""
        self.stdout.write(self.style.SUCCESS(f'\n👨‍🎓 Creating {count} sample students...'))
        
        student_group = Group.objects.get(name='Students')
        students_created = 0
        
        student_names = [
            ('john_doe', 'John', 'Doe', 'john.doe@example.com'),
            ('jane_smith', 'Jane', 'Smith', 'jane.smith@example.com'),
            ('bob_johnson', 'Bob', 'Johnson', 'bob.johnson@example.com'),
            ('alice_williams', 'Alice', 'Williams', 'alice.williams@example.com'),
            ('charlie_brown', 'Charlie', 'Brown', 'charlie.brown@example.com'),
            ('emily_davis', 'Emily', 'Davis', 'emily.davis@example.com'),
            ('michael_wilson', 'Michael', 'Wilson', 'michael.wilson@example.com'),
            ('sarah_taylor', 'Sarah', 'Taylor', 'sarah.taylor@example.com'),
            ('david_anderson', 'David', 'Anderson', 'david.anderson@example.com'),
            ('lisa_martinez', 'Lisa', 'Martinez', 'lisa.martinez@example.com'),
        ]
        
        for i in range(min(count, len(student_names))):
            username, first, last, email = student_names[i]
            
            try:
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'first_name': first,
                        'last_name': last,
                    }
                )
                
                if created:
                    user.set_password(password)
                    user.save()
                    user.groups.add(student_group)
                    students_created += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {username} ({first} {last})'))
                else:
                    self.stdout.write(self.style.WARNING(f'  ⚠️ Already exists: {username}'))
                    
            except IntegrityError:
                self.stdout.write(self.style.ERROR(f'  ❌ Error creating: {username}'))
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {students_created} new students'))

    def create_sample_officers(self, count, password):
        """Create sample officer users"""
        self.stdout.write(self.style.SUCCESS(f'\n👨‍💼 Creating {count} sample officers...'))
        
        officer_group = Group.objects.get(name='Admission Officers')
        officers_created = 0
        
        officer_names = [
            ('officer1', 'Sarah', 'Miller', 'sarah.miller@college.edu'),
            ('officer2', 'Michael', 'Davis', 'michael.davis@college.edu'),
        ]
        
        for i in range(min(count, len(officer_names))):
            username, first, last, email = officer_names[i]
            
            try:
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'first_name': first,
                        'last_name': last,
                        'is_staff': True,
                    }
                )
                
                if created:
                    user.set_password(password)
                    user.save()
                    user.groups.add(officer_group)
                    officers_created += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {username} ({first} {last})'))
                else:
                    self.stdout.write(self.style.WARNING(f'  ⚠️ Already exists: {username}'))
                    
            except IntegrityError:
                self.stdout.write(self.style.ERROR(f'  ❌ Error creating: {username}'))
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {officers_created} new officers'))

    def create_sample_courses(self, count):
        """Create sample courses"""
        self.stdout.write(self.style.SUCCESS(f'\n📚 Creating {count} sample courses...'))
        
        courses_data = [
            {
                'code': 'CS101',
                'name': 'Bachelor of Computer Science',
                'department': 'Computer Science',
                'course_type': 'UG',
                'duration': 4,
                'total_seats': 60,
                'filled_seats': 45,
                'min_percentage': 75.0,
                'fee_per_year': 50000.00,
                'description': 'Comprehensive computer science program covering algorithms, data structures, software engineering, and AI.',
                'eligibility_criteria': '12th grade with Mathematics and minimum 75% aggregate'
            },
            {
                'code': 'MBA202',
                'name': 'Master of Business Administration',
                'department': 'Business Administration',
                'course_type': 'PG',
                'duration': 2,
                'total_seats': 120,
                'filled_seats': 110,
                'min_percentage': 65.0,
                'fee_per_year': 75000.00,
                'description': 'Advanced business management program with specializations in Marketing, Finance, and HR.',
                'eligibility_criteria': 'Bachelor\'s degree with minimum 65% aggregate'
            },
            {
                'code': 'ME105',
                'name': 'Bachelor of Mechanical Engineering',
                'department': 'Mechanical Engineering',
                'course_type': 'UG',
                'duration': 4,
                'total_seats': 80,
                'filled_seats': 72,
                'min_percentage': 70.0,
                'fee_per_year': 45000.00,
                'description': 'Engineering program focusing on design, analysis, manufacturing, and maintenance of mechanical systems.',
                'eligibility_criteria': '12th grade with Physics, Chemistry, Mathematics and minimum 70% aggregate'
            },
            {
                'code': 'BCOM301',
                'name': 'Bachelor of Commerce',
                'department': 'Commerce',
                'course_type': 'UG',
                'duration': 3,
                'total_seats': 150,
                'filled_seats': 140,
                'min_percentage': 60.0,
                'fee_per_year': 35000.00,
                'description': 'Commerce program covering accounting, finance, economics, and business management.',
                'eligibility_criteria': '12th grade with minimum 60% aggregate'
            },
            {
                'code': 'DCA401',
                'name': 'Diploma in Computer Applications',
                'department': 'Computer Science',
                'course_type': 'DIP',
                'duration': 1,
                'total_seats': 40,
                'filled_seats': 25,
                'min_percentage': 55.0,
                'fee_per_year': 25000.00,
                'description': 'Practical diploma program focusing on computer applications and basic programming.',
                'eligibility_criteria': '12th grade with minimum 55% aggregate'
            },
            {
                'code': 'MA501',
                'name': 'Master of Arts in English',
                'department': 'English',
                'course_type': 'PG',
                'duration': 2,
                'total_seats': 50,
                'filled_seats': 32,
                'min_percentage': 60.0,
                'fee_per_year': 30000.00,
                'description': 'Advanced study of English literature, linguistics, and critical theory.',
                'eligibility_criteria': 'Bachelor\'s degree in English or related field with minimum 60% aggregate'
            },
            {
                'code': 'BSC102',
                'name': 'Bachelor of Science in Physics',
                'department': 'Physics',
                'course_type': 'UG',
                'duration': 3,
                'total_seats': 60,
                'filled_seats': 48,
                'min_percentage': 65.0,
                'fee_per_year': 40000.00,
                'description': 'Science program with focus on physics, mathematics, and experimental sciences.',
                'eligibility_criteria': '12th grade with Physics, Chemistry, Mathematics and minimum 65% aggregate'
            },
            {
                'code': 'LLB601',
                'name': 'Bachelor of Laws',
                'department': 'Law',
                'course_type': 'UG',
                'duration': 5,
                'total_seats': 100,
                'filled_seats': 85,
                'min_percentage': 70.0,
                'fee_per_year': 60000.00,
                'description': 'Professional law degree program covering constitutional law, criminal law, and legal procedures.',
                'eligibility_criteria': '12th grade with minimum 70% aggregate'
            }
        ]
        
        courses_created = 0
        for i in range(min(count, len(courses_data))):
            course_data = courses_data[i]
            try:
                course, created = Course.objects.get_or_create(
                    code=course_data['code'],
                    defaults=course_data
                )
                if created:
                    courses_created += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {course_data["code"]} - {course_data["name"]}'))
                else:
                    self.stdout.write(self.style.WARNING(f'  ⚠️ Already exists: {course_data["code"]}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Error creating {course_data["code"]}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {courses_created} new courses'))

    def create_sample_applications(self):
        """Create sample applications"""
        self.stdout.write(self.style.SUCCESS('\n📝 Creating sample applications...'))
        
        students = User.objects.filter(groups__name='Students')
        courses = Course.objects.all()
        officers = User.objects.filter(groups__name='Admission Officers')
        
        if not students or not courses:
            self.stdout.write(self.style.WARNING('  ⚠️ No students or courses found. Skipping applications.'))
            return
        
        statuses = ['DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'REJECTED']
        applications_created = 0
        seat_allocations_created = 0
        
        for student in students:
            # Each student applies to 1-3 random courses
            num_applications = random.randint(1, 3)
            selected_courses = random.sample(list(courses), min(num_applications, len(courses)))
            
            for course in selected_courses:
                status = random.choice(statuses)
                
                # Check eligibility (random percentage around course requirement)
                percentage = random.uniform(
                    max(30, course.min_percentage - 15),
                    min(100, course.min_percentage + 20)
                )
                is_eligible = percentage >= course.min_percentage
                
                try:
                    application, created = Application.objects.get_or_create(
                        student=student,
                        course=course,
                        defaults={
                            'previous_school': f'{random.choice(["City", "Central", "Public", "International"])} School #{random.randint(1, 50)}',
                            'previous_qualification': '12th Grade' if course.course_type == 'UG' else 'Bachelor\'s Degree',
                            'percentage_obtained': round(percentage, 2),
                            'year_of_passing': random.randint(2018, 2024),
                            'date_of_birth': timezone.now().date() - timedelta(days=random.randint(18*365, 25*365)),
                            'address': f'{random.randint(1, 999)} {random.choice(["Main St", "Park Ave", "Oak Road", "College Lane"])}, {random.choice(["New York", "Los Angeles", "Chicago", "Boston", "Seattle"])}, {random.choice(["NY", "CA", "IL", "MA", "WA"])} {random.randint(10000, 99999)}',
                            'phone': f'+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}',
                            'emergency_contact': f'+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}',
                            'status': status,
                            'is_eligible': is_eligible,
                            'eligibility_notes': f'Student obtained {percentage:.2f}% against minimum requirement of {course.min_percentage}%.',
                        }
                    )
                    
                    if created:
                        applications_created += 1
                        
                        # Set submission date for non-draft applications
                        if status != 'DRAFT':
                            application.submission_date = timezone.now() - timedelta(days=random.randint(1, 30))
                            application.save()
                            
                            # Create seat allocation for approved eligible applications
                            if status == 'APPROVED' and is_eligible and course.available_seats > 0 and officers.exists():
                                officer = random.choice(officers)
                                try:
                                    seat, seat_created = SeatAllocation.objects.get_or_create(
                                        application=application,
                                        defaults={
                                            'course': course,
                                            'allocated_by': officer,
                                            'is_confirmed': random.choice([True, False]),
                                            'confirmation_deadline': timezone.now().date() + timedelta(days=random.randint(7, 21))
                                        }
                                    )
                                    if seat_created:
                                        seat_allocations_created += 1
                                        # Update filled seats
                                        course.filled_seats += 1
                                        course.save()
                                except Exception as e:
                                    self.stdout.write(self.style.ERROR(f'  ❌ Error creating seat allocation: {str(e)}'))
                        
                        self.stdout.write(self.style.SUCCESS(f'  ✓ Created application: {application.application_number}'))
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ❌ Error creating application: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {applications_created} new applications'))
        self.stdout.write(self.style.SUCCESS(f'✓ Created {seat_allocations_created} new seat allocations'))

    def show_summary(self):
        """Show summary of created data"""
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('📊 SUMMARY'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        # Count totals
        total_students = User.objects.filter(groups__name='Students').count()
        total_officers = User.objects.filter(groups__name='Admission Officers').count()
        total_courses = Course.objects.count()
        total_applications = Application.objects.count()
        total_seats = SeatAllocation.objects.count()
        
        self.stdout.write(self.style.SUCCESS(f'👨‍🎓 Students: {total_students}'))
        self.stdout.write(self.style.SUCCESS(f'👨‍💼 Officers: {total_officers}'))
        self.stdout.write(self.style.SUCCESS(f'📚 Courses: {total_courses}'))
        self.stdout.write(self.style.SUCCESS(f'📝 Applications: {total_applications}'))
        self.stdout.write(self.style.SUCCESS(f'🪑 Seat Allocations: {total_seats}'))
        
        self.stdout.write(self.style.SUCCESS('\n🔐 LOGIN CREDENTIALS:'))
        self.stdout.write(self.style.SUCCESS('   Students: username: john_doe, password: password123'))
        self.stdout.write(self.style.SUCCESS('   Officers: username: officer1, password: password123'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Sample data population completed successfully!'))
        self.stdout.write(self.style.SUCCESS('='*60))