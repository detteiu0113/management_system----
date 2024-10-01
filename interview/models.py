from django.db import models
from accounts.models import CustomUser

class Interview(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f'{self.name} {self.start_date} - {self.end_date}'
    
class TimeChoice(models.Model):
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE)
    key = models.IntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f'{self.key} {self.start_time} - {self.end_time}'
    
class InterviewRequest(models.Model):
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE)
    parent = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.ForeignKey(TimeChoice, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)
    is_scheduled = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.parent} - {self.time}'
    
class InterviewSchdule(models.Model):
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.ForeignKey(TimeChoice, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.owner} - {self.time}'
       