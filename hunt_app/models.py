from django.db import models

class Group(models.Model):
    group_number = models.IntegerField(primary_key=True)
    group_name = models.TextField(null=True)
    licu = models.BooleanField(default=False)
    total_points = models.IntegerField(default=0)
    answers_provided = models.IntegerField(default=0)
    completion_order = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Group {self.group_number}"

class Question(models.Model):
    QUESTION_TYPES = [
        ('dropdown', 'Dropdown'),
        ('text', 'Text'),
    ]

    question_number = models.IntegerField(primary_key=True)
    question_location = models.TextField(default='')
    question_text = models.TextField()
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES)
    options = models.TextField(blank=True, null=True)  # JSON string if dropdown
    correct_answer = models.TextField()
    points = models.IntegerField(default=10)
    licu = models.BooleanField(default=False)

    def __str__(self):
        return f"Question {self.question_number}"

class Answer(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField()
    points_earned = models.IntegerField()
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Group {self.group.group_number} - Question {self.question.question_number}"
