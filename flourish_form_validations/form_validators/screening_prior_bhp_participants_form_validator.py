from django.core.exceptions import ValidationError
from edc_constants.constants import NO, UNKNOWN, NOT_APPLICABLE
from edc_form_validators import FormValidator


class ScreeningPriorBhpParticipantsFormValidator(FormValidator):

    def clean(self):
        self.validate_child_alive()
        self.validate_participation()
        self.validate_reason_not_to_participate()
        self.validate_reason_not_to_participate_other()

    def validate_participation(self):
        cleaned_data = self.cleaned_data
        mother_alive = cleaned_data.get('mother_alive')
        flourish_participation = cleaned_data.get('flourish_participation')
        if mother_alive and mother_alive in [NO, UNKNOWN]:
            if flourish_participation == 'interested':
                message = {'flourish_participation':
                               'The mother from the previous study is not alive, '
                               'Please correct interest for `another caregiver`. '}
                self._errors.update(message)
                raise ValidationError(message)

    def validate_child_alive(self):
        self.not_applicable_if(
            NO,
            field='child_alive',
            field_applicable='mother_alive')

        self.not_applicable(
            NO,
            field='child_alive',
            field_applicable='flourish_participation')

    def validate_reason_not_to_participate(self):
        self.applicable_if(NO, field='flourish_participation',
                           field_applicable='reason_not_to_participate')

    def validate_reason_not_to_participate_other(self):
        self.validate_other_specify(
            field='reason_not_to_participate',
            other_specify_field='reason_not_to_participate_other'
        )

    def not_applicable_only(self, *responses, field=None, field_applicable=None):
        cleaned_data = self.cleaned_data
        if (cleaned_data.get(field) in responses
                and cleaned_data.get(field_applicable) != NOT_APPLICABLE):
            message = {field_applicable: 'This field is not applicable'}
            self._errors.update(message)
            raise ValidationError(message)

    def applicable_only(self, *responses, field=None, field_applicable=None):
        cleaned_data = self.cleaned_data
        if (cleaned_data.get(field) in responses
                and cleaned_data.get(field_applicable) == NOT_APPLICABLE):
            message = {field_applicable: 'This field is applicable'}
            self._errors.update(message)
            raise ValidationError(message)
