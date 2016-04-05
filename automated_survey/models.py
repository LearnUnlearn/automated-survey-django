from django.db import models
from django.core.exceptions import ValidationError


class Survey(models.Model):
    title = models.CharField(max_length=255)

    @property
    def responses(self):
        return QuestionResponse.objects.filter(question__survey__id=self.id)

    def __str__(self):
        return '%s' % self.title


class Question(models.Model):
    TEXT = 'text'
    YES_NO = 'yes-no'
    NUMERIC = 'numeric'

    QUESTION_KIND_CHOICES = (
        (TEXT, 'Text'),
        (YES_NO, 'Yes or no'),
        (NUMERIC, 'Numeric')
    )

    body = models.CharField(max_length=255)
    kind = models.CharField(max_length=255, choices=QUESTION_KIND_CHOICES)
    survey = models.ForeignKey(Survey)

    @classmethod
    def validate_kind(cls, kind):
        if kind not in [cls.YES_NO, cls.NUMERIC, cls.TEXT]:
            raise ValidationError("Invalid question kind")

    def next(self):
        survey = Survey.objects.get(id=self.survey_id)

        next_questions = \
            survey.question_set.order_by('id').filter(id__gt=self.id)

        return next_questions[0] if next_questions else None

    def __str__(self):
        return '%s' % self.body


class QuestionResponse(models.Model):
    response = models.CharField(max_length=255)
    call_sid = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)
    question = models.ForeignKey(Question)

    @classmethod
    def from_twilio_request(cls, request):
        return cls(call_sid=request.POST['CallSid'],
                   phone_number=request.POST['From'],
                   response=cls._extract_content(request))

    @classmethod
    def _extract_content(cls, request):
        question_kind = request.GET.get('Kind')
        Question.validate_kind(question_kind)
        if question_kind in [Question.YES_NO, Question.NUMERIC]:
            return request.POST['Digits']
        return request.POST['RecordingUrl']

    def __str__(self):
        return '%s' % self.response

    def as_dict(self):
        return {
                'body': self.question.body,
                'kind': self.question.kind,
                'response': self.response,
                'call_sid': self.call_sid,
                'phone_number': self.phone_number,
                }
