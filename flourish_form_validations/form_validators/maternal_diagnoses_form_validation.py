from django.core.exceptions import ValidationError
from edc_constants.constants import YES, NOT_APPLICABLE, POS, OTHER
from edc_form_validators.form_validator import FormValidator
from flourish_caregiver.helper_classes import MaternalStatusHelper
from .crf_form_validator import FormValidatorMixin


class MaternalDiagnosesFormValidator(FormValidatorMixin, FormValidator):

    def clean(self):
        subject_status = self.maternal_status_helper.hiv_status

        self.subject_identifier = self.cleaned_data.get(
            'maternal_visit').subject_identifier
        super().clean()

        self.m2m_required(
            m2m_field='diagnoses')

        self.m2m_na_validation(
            field='new_diagnoses',
            m2m_field='diagnoses',
            na_response='mdiag_na',
            msg=('Participant has new diagnoses, '
                 'please give a diagnosis'),
            na_msg=('Participant has no new diagnoses, '
                    'diagnosis should be N/A'))

        self.m2m_other_specify(
            OTHER,
            m2m_field='diagnoses',
            field_other='diagnoses_other')

        self.m2m_required(
            m2m_field='who')

        self.applicable_if_true(subject_status == POS,
                                field_applicable='has_who_dx')

        self.m2m_na_validation(
            field='has_who_dx',
            m2m_field='who',
            na_response='who_na',
            msg=('WHO Stage III/IV cannot have Not Applicable in the list. '
                 'Please correct.'),
            na_msg=('WHO diagnoses is {}, WHO Stage III/IV should be Not '
                    'Applicable.'.format(self.cleaned_data.get('has_who_dx')))
        )

    def m2m_na_validation(self, field=None, m2m_field=None, msg=None,
                          na_msg=None, na_response=None):
        qs = self.cleaned_data.get(m2m_field).values_list(
            'short_name', flat=True)
        selection = list(qs.all())
        if self.cleaned_data.get(field) == YES:
            if na_response in selection:
                message = {m2m_field: msg}
                self._errors.update(message)
                raise ValidationError(message)
        else:
            if na_response not in selection:
                message = {m2m_field: na_msg}
                self._errors.update(message)
                raise ValidationError(message)

            self.m2m_single_selection_if(
                na_response,
                m2m_field=m2m_field
            )

    @property
    def maternal_status_helper(self):
        cleaned_data = self.cleaned_data
        status_helper = MaternalStatusHelper(
            cleaned_data.get('maternal_visit'))
        return status_helper
