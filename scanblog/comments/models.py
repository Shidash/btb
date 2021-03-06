import datetime
from django.db import models
from django.contrib.auth.models import User

from btb.utils import OrgManager, OrgQuerySet

class CommentManager(OrgManager):
    def public(self):
        return self.filter(removed=False, document__status="published")

    def excluding_boilerplate(self):
        return self.public().exclude(
                comment="Thanks for writing! I finished the transcription for your post."
            ).exclude(
                comment="Thanks for writing! I worked on the transcription for your post."
            ).exclude(
                comment_doc__isnull=False
            )


    def with_mailed_annotation(self):
        return self.public().annotate(letter_sent=models.Max('letter__sent'))

    def unmailed(self):
        return self.public().filter(
            comment_doc__isnull=True,
            document__isnull=False,
            document__author__is_active=True,
            document__author__profile__managed=True,
            letter__isnull=True,
        )

class Comment(models.Model):
    user = models.ForeignKey(User)
    created = models.DateTimeField(default=datetime.datetime.now)
    modified = models.DateTimeField(default=datetime.datetime.now)

    # The comment itself
    comment = models.TextField(blank=True)
    comment_doc = models.OneToOneField('scanning.Document', 
            null=True, blank=True)
    document = models.ForeignKey('scanning.Document', blank=True, null=True,
            related_name='comments')

    # Metadata
    ip_address = models.IPAddressField(blank=True, null=True)
    removed = models.BooleanField()

    objects = CommentManager()

    def clean(self):
        # Deal with https://code.djangoproject.com/ticket/5622
        if not self.ip_address:
            self.ip_address = None

    class QuerySet(OrgQuerySet):
        orgs = ["document__author__organization"]

    def get_absolute_url(self):
        if self.document:
            return "%s#c%s" % (self.document.get_absolute_url(), self.pk)
        return ""

    def to_dict(self):
        cd = self.comment_doc
        return {
            'id': self.pk,
            'user': self.user.profile.to_dict(),
            'created': self.created.isoformat(),
            'modified': self.modified.isoformat(),
            'comment': self.comment,
            'comment_doc': cd.to_dict() if cd else None,
            'removed': self.removed,
            'url': self.get_absolute_url(),
            'edit_url': self.get_absolute_url(),
        }

    class Meta:
        ordering = ['created']

    def __unicode__(self):
        if self.comment:
            blurb = self.comment[:50] + "..."
        elif self.comment_doc:
            blurb = "<doc %i>" % self.comment_doc.pk
        else:
            blurb = "None"
        return "%s: %s" % (self.user.profile.display_name, blurb)

class Favorite(models.Model):
    user = models.ForeignKey(User)
    document = models.ForeignKey('scanning.Document')
    created = models.DateTimeField(default=datetime.datetime.now)

    class QuerySet(OrgQuerySet):
        orgs = ["document__author__organization"]

    def get_absolute_url(self):
        return self.document.get_absolute_url()

    def to_dict(self):
        return {
                'id': self.pk,
                'user_id': self.user_id,
                'document_id': self.document_id,
                'url': self.get_absolute_url(),
        }

    class Meta:
        ordering = ['-created']

    def __unicode__(self):
        return "%s: %s" % (self.user.profile, self.document_id)
