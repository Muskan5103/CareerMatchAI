
from django import forms
from .models import Job


class JobForm(forms.ModelForm):
    required_skills = forms.CharField(
    required=False,
    widget=forms.TextInput(attrs={
        "class": "form-input",
        "placeholder": "Python, Django, PostgreSQL",
    }),
)
    class Meta:
        model = Job
        fields = [
            "title",
            "company_name",
            "description",
            "required_skills",
            "location",
            "job_type",
            "experience_level",
            "min_salary",
            "max_salary",
        ]

        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "e.g. Junior Python Developer",
            }),
            "company_name": forms.TextInput(attrs={
                "class": "form-input",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-input",
                "rows": 6,
            }),
            "required_skills": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Python, Django, PostgreSQL",
            }),
            "location": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Amritsar or Remote",
            }),
            "job_type": forms.Select(attrs={
                "class": "form-input",
            }),
            "experience_level": forms.Select(attrs={
                "class": "form-input",
            }),
            "min_salary": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 0,
            }),
            "max_salary": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 0,
            }),
        }

    def clean_required_skills(self):
        raw = self.cleaned_data.get("required_skills")

        if isinstance(raw, list):
            skills = raw
        else:
            skills = raw.split(",") if raw else []

        skills = list(dict.fromkeys(
            skill.strip() for skill in skills if skill.strip()
        ))

        if len(skills) > 50:
            raise forms.ValidationError("Enter no more than 50 skills.")

        if any(len(skill) > 60 for skill in skills):
            raise forms.ValidationError(
                "Each skill must be 60 characters or fewer."
            )

        return skills

    def clean(self):
        cleaned_data = super().clean()
        minimum = cleaned_data.get("min_salary")
        maximum = cleaned_data.get("max_salary")

        if (
            minimum is not None
            and maximum is not None
            and maximum < minimum
        ):
            self.add_error(
                "max_salary",
                "Maximum salary must be at least the minimum salary.",
            )

        return cleaned_data
