from django.db import models

# Create your models here.
ALGORITHM_CHOICES = [
    ("token_bucket", "Token Bucket"),
    ("fixed_window", "Fixed Window"),
]

class RouteLimit(models.Model):
    route = models.CharField(max_length=255, unique=True)
    capacity = models.PositiveIntegerField(default=10)
    refill_rate = models.FloatField(default=1)
    algorithm = models.CharField(
        max_length=20,
        choices= ALGORITHM_CHOICES,
        default= "token_bucket",
    )

    enabled = models.BooleanField(default= True)

    def __str__(self):
        return self.route