from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Course(models.Model):
    COURSE_TYPES = [
        ('UG', 'Undergraduate'),
        ('PG', 'Postgraduate'),
        ('DIP', 'Diploma'),
    ]
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    description = models.TextField()
    duration = models.IntegerField(help_text="Duration in years")
    course_type = models.CharField(max_length=10, choices=COURSE_TYPES)
    total_seats = models.IntegerField(default=60)
    filled_seats = models.IntegerField(default=0)
    min_percentage = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    eligibility_criteria = models.TextField()
    fee_per_year = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def available_seats(self):
        return self.total_seats - self.filled_seats
    
    @property
    def seat_percentage(self):
        if self.total_seats == 0:
            return 0
        return (self.filled_seats / self.total_seats) * 100
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    class Meta:
        ordering = ['code']


class Application(models.Model):
    APPLICATION_STATUS = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('SHORTLISTED', 'Shortlisted'),
        ('REJECTED', 'Rejected'),
        ('APPROVED', 'Approved'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='applications')
    application_number = models.CharField(max_length=20, unique=True, editable=False)
    previous_school = models.CharField(max_length=200)
    previous_qualification = models.CharField(max_length=100)
    percentage_obtained = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    year_of_passing = models.IntegerField()
    date_of_birth = models.DateField()
    address = models.TextField()
    phone = models.CharField(max_length=15)
    emergency_contact = models.CharField(max_length=15)
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS, default='DRAFT')
    submission_date = models.DateTimeField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_applications')
    review_date = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    is_eligible = models.BooleanField(default=False)
    eligibility_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['student', 'course']
    
    def save(self, *args, **kwargs):
        if not self.application_number:
            year = timezone.now().year
            last_app = Application.objects.filter(created_at__year=year).count()
            self.application_number = f"APP{year}{last_app + 1:05d}"
        
        if self.status == 'SUBMITTED' and not self.submission_date:
            self.submission_date = timezone.now()
            
        super().save(*args, **kwargs)
    
   
    @classmethod
    def can_apply(cls, student, course):
        existing = cls.objects.filter(
            student=student,
            course=course
        ).exists()
        
        if existing:
            return False, "❌ You have already applied to this course"
        
        return True, "✅ You can apply to this course"
    
   
    @classmethod
    def get_active_count(cls, student):
        return cls.objects.filter(
            student=student,
            status__in=['DRAFT', 'SUBMITTED', 'UNDER_REVIEW']
        ).count()
    
    @classmethod
    def can_create_more(cls, student, limit=3):
        active_count = cls.get_active_count(student)
        if active_count >= limit:
            return False, f"❌ You already have {active_count} active applications. Maximum limit is {limit}."
        return True, f"✅ You can create {limit - active_count} more applications"
    
    def __str__(self):
        return f"{self.application_number} - {self.student.username}"


class SeatAllocation(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='seat_allocation')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='seat_allocations')
    allocation_date = models.DateTimeField(auto_now_add=True)
    allocated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_confirmed = models.BooleanField(default=False)
    confirmation_deadline = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    
    @classmethod
    def can_allocate(cls, application):
        has_seat = cls.objects.filter(
            application__student=application.student
        ).exists()
        
        if has_seat:
            return False, "❌ Student already has an allocated seat"
        
        return True, "✅ Student can get seat"
    
    def __str__(self):
        return f"Seat for {self.application.application_number}"
    
    class Meta:
        ordering = ['-allocation_date']