"""
incidents table — matches what workers/incidentExpiryWorker.js assumed
(status, expires_at columns), extended with the fields the Blog Feed
mockup actually needs: photo, title/description, category, location,
and a credibility score driven by votes.
"""
from django.db import models
from accounts.models import User
from django.contrib.gis.db import models as gis_models
from django.db import models

class Incident(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50)
    photo = models.ImageField(upload_to='incidents/', null=True, blank=True)
    
    # PostGIS Spatial Point (srid=4326 for standard WGS84 GPS coordinates)
    location = gis_models.PointField(srid=4326, spatial_index=True)
    
    credibility_score = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'incidents'

class Incident(models.Model):
    CATEGORY_CHOICES = [
        ("accident", "Accident"),
        ("roadwork", "Roadwork"),
        ("flooding", "Flooding"),
        ("hazard", "Hazard"),
        ("other", "Other"),
    ]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("resolved", "Resolved"),
        ("expired", "Expired"),
    ]

    reporter = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="incidents"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=16, choices=CATEGORY_CHOICES, default="other")
    photo = models.ImageField(upload_to="incidents/%Y/%m/", null=True, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="active", db_index=True)
    credibility_score = models.IntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "incidents"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class IncidentVote(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="incident_votes")
    value = models.SmallIntegerField()  # +1 upvote, -1 downvote
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "incident_votes"
        unique_together = ("incident", "user")  # one vote per user per incident

    def __str__(self):
        return f"{self.user_id} -> {self.incident_id}: {self.value}"
