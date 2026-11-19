from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import get_user_role


class RoleAuthenticationForm(AuthenticationForm):
    expected_role = None

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if get_user_role(user) != self.expected_role:
            raise ValidationError(
                'This account cannot sign in through this page. '
                'Please use the correct sign-in page.',
                code='invalid_login',
            )


class CitizenAuthenticationForm(RoleAuthenticationForm):
    expected_role = 'citizen'


class OfficerAuthenticationForm(RoleAuthenticationForm):
    expected_role = 'officer'


class CitizenRegistrationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ('username', 'email')
