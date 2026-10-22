
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import User


class BaseRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "form-input",
            "placeholder": "Enter your email address",
        }),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].strip()

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")

        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].strip()
        user.role = self.role

        if commit:
            user.save()

        return user


class CandidateRegistrationForm(BaseRegistrationForm):
    role = User.Role.CANDIDATE


class RecruiterRegistrationForm(BaseRegistrationForm):
    role = User.Role.RECRUITER

    company_name = forms.CharField(
        max_length=200,
        label="Company name",
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "Enter your company name",
        }),
    )

    designation = forms.CharField(
        max_length=100,
        required=False,
        label="Your designation",
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "e.g. HR Manager",
        }),
    )



from django import forms
from .models import CandidateProfile, RecruiterProfile


class CandidateProfileForm(forms.ModelForm):
    skills = forms.CharField(
        required=False,
        help_text="Enter skills separated by commas, e.g. Python, Django, SQL.",
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "Python, Django, PostgreSQL",
        }),
    )

    class Meta:
        model = CandidateProfile
        fields = [
            "full_name",
            "phone",
            "location",
            "education",
            "skills",
            "experience_years",
            "linkedin_url",
            "github_url",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-input"}),
            "phone": forms.TextInput(attrs={"class": "form-input"}),
            "location": forms.TextInput(attrs={"class": "form-input"}),
            "education": forms.TextInput(attrs={"class": "form-input"}),
            "experience_years": forms.NumberInput(
                attrs={"class": "form-input", "min": 0, "max": 60}
            ),
            "linkedin_url": forms.URLInput(attrs={"class": "form-input"}),
            "github_url": forms.URLInput(attrs={"class": "form-input"}),
        }

    def clean_skills(self):
        raw = self.cleaned_data.get("skills", "")
        skills = list(dict.fromkeys(
            skill.strip() for skill in raw.split(",") if skill.strip()
        ))

        if len(skills) > 50:
            raise forms.ValidationError("Enter no more than 50 skills.")

        if any(len(skill) > 60 for skill in skills):
            raise forms.ValidationError(
                "Each skill must be 60 characters or fewer."
            )

        return skills

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()

        if phone and len(phone) > 20:
            raise forms.ValidationError("Phone number is too long.")

        return phone


class RecruiterProfileForm(forms.ModelForm):
    class Meta:
        model = RecruiterProfile
        fields = [
            "company_name",
            "designation",
            "company_website",
            "company_description",
        ]
        widgets = {
            "company_name": forms.TextInput(attrs={"class": "form-input"}),
            "designation": forms.TextInput(attrs={"class": "form-input"}),
            "company_website": forms.URLInput(attrs={"class": "form-input"}),
            "company_description": forms.Textarea(
                attrs={"class": "form-input", "rows": 5}
            ),
        }

    def clean_company_name(self):
        name = self.cleaned_data["company_name"].strip()

        if not name:
            raise forms.ValidationError("Company name is required.")

        return name
