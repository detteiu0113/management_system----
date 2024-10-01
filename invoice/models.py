from django.db import models
from students.models import Student
from accounts.models import CustomUser

class Invoice(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE) 
    cost_name = models.CharField(max_length=100)
    price = models.IntegerField(null=True, blank=True)  
    date = models.DateField()

    def __str__(self):
        return f'{self.student} {self.cost_name} {self.price} {self.date}'
    
class PaidInvoice(models.Model):
    parent = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField()
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.parent} {self.date.year} {self.date.month}'
