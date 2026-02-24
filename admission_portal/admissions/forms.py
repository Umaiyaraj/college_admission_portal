from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Application, Course
from django.core.exceptions import ValidationError
from datetime import date
from django.utils import timezone

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields =[
            'course',
            'previous_school',
            'previous_qualification',
            'percentage_obtained',
            'year_of_passing',
            'date_of_birth',
            'address',
            'phone',
            'emergency_contact',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

        previous_qualification = [
            ('12th', '12th Standard'),
            ('Diploma', 'Diploma'),
            ]
    
    def clean_percentage_obtained(self):
        percentage = self.cleaned_data['percentage_obtained']
        if percentage < 0 or percentage > 100:
            raise ValidationError("Percentage must be between 0 and 100")
        return percentage
    
    def clean_year_of_passing(self):
        year = self.cleaned_data['year_of_passing']
        current_year = timezone.now().year
        if year < 1900 or year > current_year:
            raise ValidationError(f"Year must be between 1900 and {current_year}")
        return year

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        today = date.today()

        if dob > today:
            raise forms.ValidationError("Date of birth cannot be in the future.")

        age = today.year - dob.year - (
            (today.month, today.day) < (dob.month, dob.day)
        )

        if age < 16:
            raise forms.ValidationError("You must be at least 16 years old to apply.")

        return dob

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')

        if not phone.isdigit():
            raise forms.ValidationError(
                "Phone number must contain only digits."
            )

        if len(phone) != 10:
            raise forms.ValidationError(
                "Phone number must be exactly 10 digits."
            )

        return phone

    def clean_emergency_contact(self):
        contact = self.cleaned_data.get('emergency_contact')

        if not contact.isdigit():
            raise forms.ValidationError(
                "Emergency contact must contain only digits."
            )

        if len(contact) != 10:
            raise forms.ValidationError(
                "Emergency contact must be exactly 10 digits."
            )

        return contact

class ReviewApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['status', 'review_notes', 'is_eligible', 'eligibility_notes']
        widgets = {
            'review_notes': forms.Textarea(attrs={'rows': 4}),
            'eligibility_notes': forms.Textarea(attrs={'rows': 4}),
        }

class CourseSearchForm(forms.Form):
    name = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Course name...'}))
    department = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Department...'}))
    course_type = forms.ChoiceField(required=False, choices=[('', 'All Types')] + Course.COURSE_TYPES)

class ApplicationFilterForm(forms.Form):
    status = forms.ChoiceField(required=False, choices=[('', 'All Status')] + Application.APPLICATION_STATUS)
    course = forms.ModelChoiceField(required=False, queryset=Course.objects.all(), empty_label="All Courses")
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'code', 'name', 'department', 'description',
            'duration', 'course_type', 'total_seats', 
            'min_percentage', 'fee_per_year', 'eligibility_criteria'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'eligibility_criteria': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean_code(self):
        code = self.cleaned_data['code']
        return code.upper()
    
    def clean_min_percentage(self):
        percentage = self.cleaned_data.get('min_percentage')
        if percentage < 0 or percentage > 100:
            raise forms.ValidationError("Minimum percentage must be between 0 and 100.")
        return percentage
    
    def clean_fee_per_year(self):
        fee = self.cleaned_data.get('fee_per_year')
        if fee <= 0:
            raise forms.ValidationError("Fee must be greater than 0.")
        return fee
