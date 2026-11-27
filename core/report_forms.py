from django import forms

from .models import Project, ProjectReport


class ProjectReportForm(forms.ModelForm):
    class Meta:
        model = ProjectReport
        fields = ('project', 'title', 'category', 'description', 'evidence')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6}),
            'evidence': forms.ClearableFileInput(
                attrs={'accept': '.jpg,.jpeg,.png,.webp,.pdf'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.order_by(
            'county',
            'title',
        )


class ProjectReportReviewForm(forms.ModelForm):
    class Meta:
        model = ProjectReport
        fields = ('status', 'officer_response')
        widgets = {
            'officer_response': forms.Textarea(attrs={'rows': 5}),
        }
