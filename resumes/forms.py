
import zipfile

from django import forms
from django.core.exceptions import ValidationError

from .models import Resume


MAX_RESUME_SIZE = 5 * 1024 * 1024  # 5 MB


def validate_resume_file(uploaded_file):
    if uploaded_file.size > MAX_RESUME_SIZE:
        raise ValidationError("Resume must be 5 MB or smaller.")

    filename = uploaded_file.name.lower()

    try:
        uploaded_file.seek(0)

        if filename.endswith(".pdf"):
            signature = uploaded_file.read(5)
            uploaded_file.seek(0)

            if signature != b"%PDF-":
                raise ValidationError(
                    "The file does not appear to be a valid PDF."
                )

        elif filename.endswith(".docx"):
            uploaded_file.seek(0)

            if not zipfile.is_zipfile(uploaded_file):
                raise ValidationError(
                    "The file does not appear to be a valid DOCX document."
                )

            uploaded_file.seek(0)

            with zipfile.ZipFile(uploaded_file) as archive:
                names = set(archive.namelist())

                if (
                    "[Content_Types].xml" not in names
                    or "word/document.xml" not in names
                ):
                    raise ValidationError(
                        "The DOCX document structure is invalid."
                    )

        else:
            raise ValidationError(
                "Only PDF and DOCX resumes are accepted."
            )

    except (OSError, zipfile.BadZipFile):
        raise ValidationError("The uploaded file could not be read.")

    finally:
        uploaded_file.seek(0)


class ResumeUploadForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ["title", "file", "is_primary"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "e.g. Python Developer Resume",
                "maxlength": 150,
            }),
            "file": forms.ClearableFileInput(attrs={
                "class": "form-input",
                "accept": ".pdf,.docx",
            }),
        }

    def clean_title(self):
        title = self.cleaned_data["title"].strip()

        if not title:
            raise ValidationError("Please enter a resume title.")

        return title

    def clean_file(self):
        uploaded_file = self.cleaned_data.get("file")

        if uploaded_file:
            validate_resume_file(uploaded_file)

        return uploaded_file
