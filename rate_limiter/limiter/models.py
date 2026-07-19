from django.db import models

# Create your models here.
ALGORITHM_CHOICES = [
    ("token", "tocken_bucket"),
    ("fixed", "fixed_window"),
]

class RouteLimit(models.Model):
    route = models.CharField(max_length=255, unique=True)
    capacity = models.PositiveIntegerField(default=10)
    refill_rate = models.FloatField(default=1)
    algorithm = models.CharField(
        max_length=10,
        choices= ALGORITHM_CHOICES,
        default= "token",
    )

    enabled = models.BooleanField(default= True)

    def __str__(self):
        return self.route