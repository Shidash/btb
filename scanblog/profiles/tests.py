import os
import json
import datetime

from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.core.urlresolvers import reverse

from profiles.models import Profile, Organization

from scanning.models import Document, Scan
from annotations.models import Note

class TestUrls(TestCase):
    fixtures = ["initial_data.json"]
    def testAbsoluteUrls(self):
        u = User.objects.create(username="hoopla", pk=12345)
        u.profile.display_name = "Test User"
        u.profile.blogger = True
        u.save()
        self.assertEquals(u.profile.get_absolute_url(), "/people/show/12345")
        self.assertEquals(u.profile.get_blog_url(), "/blogs/12345/test-user")
        self.assertEquals(u.profile.get_bare_blog_url(), "/blogs/12345/")


class TestProfileManager(TestCase):
    fixtures = ["initial_data.json"]
    def setUp(self):
        # Remove default user from fixture.
        User.objects.get(username='uploader').delete()
        sender = User.objects.create(username="sender")
        def create_letter(recipient, ltype, sent):
            recipient.received_letters.create(
                sender=sender, 
                type=ltype, 
                sent=datetime.datetime.now() if sent else None
            )
        profiles = {
            'sender': sender.profile,
            'active_commenter': User.objects.create(
                username="active_commenter").profile,
            'inactive_commenter': User.objects.create(
                username="inactive_commenter", is_active=False).profile,
        }

        # User.is_active bit
        for active in [True, False]:
            # Profile.consent_form_received bit
            for consented in [True, False]:
                # Create letter objects with sent=None?
                for unsent_letters in [True, False]:
                    # Create consent_form letter?
                    for consent_form in [True, False]:
                        for waitlist in [True, False]:
                            key = (active, consented, unsent_letters, 
                                    consent_form, waitlist)
                            key = tuple([{True: 1, False: 0}[s] for s in key])

                            user = User.objects.create(
                                    username=",".join(str(k) for k in key),
                                    is_active=active)
                            user.profile.consent_form_received = consented
                            user.profile.blogger = True
                            user.profile.managed = True
                            user.profile.save()
                            if consent_form or unsent_letters:
                                create_letter(user, 'consent_form', 
                                              consent_form)
                            if waitlist or unsent_letters:
                                create_letter(user, "waitlist", waitlist)

                            profiles[key] = user.profile

        self.profiles = profiles
        self.sender = sender

    def assertQsContains(self, qs, profile_list):
        self.assertEquals(
            set(list(qs)), 
            set([self.profiles[p] for p in profile_list])
        )

    def test_active(self):
        self.assertQsContains(Profile.objects.active(), [
            "sender",
            "active_commenter",
            # active, consented, unsent_letters, consent_form_sent, waitlist_sent
            (1, 1, 1, 1, 1,),
            (1, 1, 1, 1, 0,),
            (1, 1, 1, 0, 1,),
            (1, 1, 0, 1, 1,),
            (1, 0, 1, 1, 1,),
            (1, 1, 1, 0, 0,),
            (1, 1, 0, 1, 0,),
            (1, 0, 1, 1, 0,),
            (1, 1, 0, 0, 1,),
            (1, 0, 1, 0, 1,),
            (1, 0, 0, 1, 1,),
            (1, 1, 0, 0, 0,),
            (1, 0, 1, 0, 0,),
            (1, 0, 0, 1, 0,),
            (1, 0, 0, 0, 1,),
            (1, 0, 0, 0, 0,),
        ])
    def test_inactive(self):
        self.assertQsContains(Profile.objects.inactive(), [
            "inactive_commenter",
            # active, consented, unsent_letters, consent_form_sent, waitlist_sent
            (0, 1, 1, 1, 1,),
            (0, 1, 1, 1, 0,),
            (0, 1, 1, 0, 1,),
            (0, 1, 0, 1, 1,),
            (0, 0, 1, 1, 1,),
            (0, 1, 1, 0, 0,),
            (0, 1, 0, 1, 0,),
            (0, 0, 1, 1, 0,),
            (0, 1, 0, 0, 1,),
            (0, 0, 1, 0, 1,),
            (0, 0, 0, 1, 1,),
            (0, 1, 0, 0, 0,),
            (0, 0, 1, 0, 0,),
            (0, 0, 0, 1, 0,),
            (0, 0, 0, 0, 1,),
            (0, 0, 0, 0, 0,),
        ])
    def test_inactive_commenters(self):
        self.assertQsContains(Profile.objects.inactive_commenters(), [
            "inactive_commenter",
        ])
    def test_inactive_bloggers(self):
        self.assertQsContains(Profile.objects.inactive_bloggers(), [
            # active, consented, unsent_letters, consent_form_sent, waitlist_sent
            (0, 1, 1, 1, 1,),
            (0, 1, 1, 1, 0,),
            (0, 1, 1, 0, 1,),
            (0, 1, 0, 1, 1,),
            (0, 0, 1, 1, 1,),
            (0, 1, 1, 0, 0,),
            (0, 1, 0, 1, 0,),
            (0, 0, 1, 1, 0,),
            (0, 1, 0, 0, 1,),
            (0, 0, 1, 0, 1,),
            (0, 0, 0, 1, 1,),
            (0, 1, 0, 0, 0,),
            (0, 0, 1, 0, 0,),
            (0, 0, 0, 1, 0,),
            (0, 0, 0, 0, 1,),
            (0, 0, 0, 0, 0,),
        ])

    def test_commenters(self):
        self.assertQsContains(Profile.objects.commenters(), [
            "sender",
            "active_commenter",
        ])
    def test_bloggers(self):
        self.assertQsContains(Profile.objects.bloggers(), [
            # active, consented, unsent_letters, consent_form_sent, waitlist_sent
            (1, 1, 1, 1, 1,),
            (1, 1, 1, 1, 0,),
            (1, 1, 1, 0, 1,),
            (1, 1, 0, 1, 1,),
            (1, 0, 1, 1, 1,),
            (1, 1, 1, 0, 0,),
            (1, 1, 0, 1, 0,),
            (1, 0, 1, 1, 0,),
            (1, 1, 0, 0, 1,),
            (1, 0, 1, 0, 1,),
            (1, 0, 0, 1, 1,),
            (1, 1, 0, 0, 0,),
            (1, 0, 1, 0, 0,),
            (1, 0, 0, 1, 0,),
            (1, 0, 0, 0, 1,),
            (1, 0, 0, 0, 0,),
        ])
    def test_enrolled(self):
        self.assertQsContains(Profile.objects.enrolled(), [
            # active, consented, unsent_letters, consent_form_sent, waitlist_sent
            (1, 1, 1, 1, 1,),
            (1, 1, 1, 1, 0,),
            (1, 1, 1, 0, 1,),
            (1, 1, 0, 1, 1,),
            (1, 1, 1, 0, 0,),
            (1, 1, 0, 1, 0,),
            (1, 1, 0, 0, 1,),
            (1, 1, 0, 0, 0,),
        ])
    def test_invited(self):
        self.assertQsContains(Profile.objects.invited(), [
            # active, consented, unsent_letters, consent_form_sent, waitlist_sent
            (1, 0, 1, 1, 1,),
            (1, 0, 1, 1, 0,),
            (1, 0, 0, 1, 1,),
            (1, 0, 1, 0, 1,),
            (1, 0, 0, 1, 0,),
            (1, 0, 1, 0, 0,),
        ])
    def test_invitable(self):
        self.assertQsContains(Profile.objects.invitable(), [
            # active, consented, unsent_letters, consent_form_sent, waitlist_sent
            (1, 0, 0, 0, 1,),
            (1, 0, 0, 0, 0,),
        ])
    def test_waitlisted(self):
        self.assertQsContains(Profile.objects.waitlisted(), [
            # active, consented, unsent_letters, consent_form_sent, waitlist_sent
            (1, 0, 0, 0, 1,),
        ])
    def test_waitlistable(self):
        self.assertQsContains(Profile.objects.waitlistable(), [
            # active, consented, unsent_letters, consent_form_sent, waitlist_sent
            (1, 0, 0, 0, 0,),
        ])

    def test_needs_signup_complete_letter(self):
        # With no letters in the test set, all enrolled folks need signup complete.
        self.assertEqual(set(Profile.objects.needs_signup_complete_letter()), 
                         set(Profile.objects.enrolled()))
        # Add a letter, and the user shouldn't be in needs_signup_complete anymore.
        p = Profile.objects.enrolled()[0]
        p.user.received_letters.create(
                sender=self.sender,
                type="signup_complete")

        self.assertTrue(p not in set(Profile.objects.needs_signup_complete_letter()))

    def test_needs_first_post_letter(self):
        # No one needs one yet, as no one has a post.
        self.assertEqual(set(Profile.objects.needs_first_post_letter()), set())

        p = Profile.objects.enrolled()[0]
        p.user.documents_authored.create(type="post", editor=self.sender, 
                status="published")
        self.assertTrue(p in Profile.objects.needs_first_post_letter())

        # Create a first post letter, then no one should need one again.
        p.user.received_letters.create(
                sender=self.sender,
                type="first_post")
        self.assertEqual(set(Profile.objects.needs_first_post_letter()), set())

    def test_needs_comments_letter(self):
        # No one needs one yet, as there are no posts or comments.
        self.assertEqual(set(Profile.objects.needs_comments_letter()), set())

        # Add a post...
        p = Profile.objects.enrolled()[0]
        doc = p.user.documents_authored.create(type="post", editor=self.sender,
                status="published")
        # ... still no one.
        self.assertEqual(set(Profile.objects.needs_comments_letter()), set())

        # Add a comment...
        comment = doc.comments.create(user=self.sender, comment="My Comment")
        # ... now we need one:
        self.assertTrue(p in set(Profile.objects.needs_comments_letter()))

        # Create a comment letter ...
        cl = p.user.received_letters.create(
                sender=self.sender,
                type="comments")
        cl.comments.add(comment)
        # ... and no one should need one anymore.
        self.assertEqual(set(Profile.objects.needs_comments_letter()), set())

    def test_bloggers_with_published_content(self):
        self.assertEqual(set(Profile.objects.bloggers_with_published_content()), set())
        has_post, has_profile, has_both, has_nothing = Profile.objects.enrolled()[0:4]
        has_post.user.documents_authored.create(type="post", editor=self.sender, 
                status="published")
        has_profile.user.documents_authored.create(type="profile", editor=self.sender,
                status="published")
        has_both.user.documents_authored.create(type="post", editor=self.sender, 
                status="published")
        has_both.user.documents_authored.create(type="profile", editor=self.sender,
                status="published")

        self.assertEqual(
            sorted(Profile.objects.bloggers_with_published_content(), key=lambda a: a.pk),
            sorted([has_post, has_profile, has_both], key=lambda a: a.pk)
        )

class TestOrgPermissions(TestCase):
    fixtures = ["initial_data.json"]
    def setUp(self):
        self.orgs = []
        self.superuser = User.objects.create(username="superuser", is_superuser=True)
        self.superuser.set_password("superuser")
        self.superuser.save()
        for i in range(2):
            org = Organization.objects.create(name="Org %s" % i, slug="org-%s" % i)
            member = User.objects.create(username="org%smember" % i)
            member.profile.display_name = "Org %s Member" % i
            member.profile.blogger = True
            member.profile.managed = True
            member.profile.consent_form_received = True
            member.profile.save()
            org.members.add(member)
            mod = User.objects.create(username="org%smod" % i)
            mod.set_password("mod")
            mod.save()
            mod.groups.add(Group.objects.get(name="moderators"))
            org.moderators.add(mod)
            self.orgs.append({
                'org': org,
                'member': member,
                'mod': mod,
            })
        self.orgs[1]['org'].outgoing_mail_handled_by = self.orgs[0]['org']
        self.orgs[1]['org'].save()

    def _org_vars(self):
        return (self.orgs[0]['org'], 
                self.orgs[0]['mod'], 
                self.orgs[0]['member'],
                self.orgs[1]['org'], 
                self.orgs[1]['mod'], 
                self.orgs[1]['member'])


    def _json_results(self, username, password, url, id_set):
        self.client.logout()
        self.assertTrue(
            self.client.login(username=username, password=password)
        )
        res = self.client.get(url)
        self.assertEquals(res.status_code, 200)
        struct = json.loads(res.content)
        result_ids = set(a['id'] for a in struct['results'])
        self.assertEquals(result_ids, id_set)

    def test_access_notes(self):
        org0, mod0, member0, org1, mod1, member1 = self._org_vars()

        def note_permissions(note, can_edit, cant_edit, filtr=None):
            self.assertTrue(note in Note.objects.all().org_filter(can_edit))
            self.assertFalse(note in Note.objects.all().org_filter(cant_edit))
            if filtr:
                self.assertTrue(note in Note.objects.filter(**filtr).org_filter(can_edit))
                self.assertFalse(note in Note.objects.filter(**filtr).org_filter(cant_edit))

        # Basic permissions

        doc = Document.objects.create(author=member0, editor=mod0)
        doc_note = doc.notes.create(creator=mod0)
        note_permissions(doc_note, mod0, mod1, {'document__isnull': False})

        scan = Scan.objects.create(author=member0, uploader=mod0, pdf="foo")
        scan_note = scan.notes.create(creator=mod0)
        note_permissions(scan_note, mod0, mod1, {'scan__isnull': False})

        user_note = member0.notes.create(creator=mod0)
        note_permissions(user_note, mod0, mod1, {"user__isnull": False})

        # JSON access

        # Moderator for group 0, or superuser
        for u, p in ((mod0.username, "mod"), ("superuser", "superuser")):
            self._json_results(u, p, 
                "/annotations/notes.json", 
                set([doc_note.id, scan_note.id, user_note.id]))
            self._json_results(u, p, 
                "/annotations/notes.json?user_id=%s" % user_note.user.id,
                set([user_note.id]))
            self._json_results(u, p, 
                "/annotations/notes.json?scan_id=%s" % scan_note.scan.id,
                set([scan_note.id]))
            self._json_results(u, p, 
                "/annotations/notes.json?document_id=%s" % doc_note.document.id,
                set([doc_note.id]))
        # Moderator for group 1
        self.assertFalse(org0 in mod1.organizations_moderated.all())
        self._json_results(mod1.username, "mod",
                "/annotations/notes.json", set([]))

    def test_access_documents(self):
        org0, mod0, member0, org1, mod1, member1 = self._org_vars()

        doc = Document.objects.create(author=member0, editor=mod0)
        self.assertEquals(
            set(Document.objects.org_filter(mod0)),
            set([doc])
        )
        self.assertEquals(
            set(Document.objects.org_filter(mod1)),
            set()
        )

        # JSON access

        c = self.client
        for u, p in ((mod0.username, "mod"), ("superuser", "superuser")):
            self._json_results(u, p,
                    "/scanning/documents.json",
                    set([doc.pk]))
        self._json_results(mod1.username, "mod", 
                "/scanning/documents.json", 
                set())
    
    def test_access_scans(self):
        org0, mod0, member0, org1, mod1, member1 = self._org_vars()

        with_author = Scan.objects.create(author=member0, uploader=mod0,
                pdf="foo", org=org0)
        self.assertEquals(set(Scan.objects.org_filter(mod0)), 
                set([with_author]))

        no_author = Scan.objects.create(uploader=mod0, pdf="foo", org=org0)
        self.assertEquals(set(Scan.objects.org_filter(mod0)), 
                set([with_author, no_author]))

        self.assertEquals(set(Scan.objects.org_filter(mod1)), set())

        # JSON access

        c = self.client
        for u, p in ((mod0.username, "mod"), ("superuser", "superuser")):
            self._json_results(u, p,
                    "/scanning/scans.json",
                    set([with_author.pk, no_author.pk])
            )
        for u, p, status in (
                    (mod0.username, "mod", 200), 
                    ("superuser", "superuser", 200),
                    (mod1.username, "mod", 403),
                ):
            self.client.logout()
            self.client.login(username=u, password=p)
            res = self.client.get("/scanning/scansplits.json/%s" % no_author.pk)
            self.assertEquals(res.status_code, status)
            if status == 200:
                struct = json.loads(res.content)
                self.assertEquals(struct['scan']['id'], no_author.pk)

    def test_mail(self):
        org0, mod0, member0, org1, mod1, member1 = self._org_vars()

        # org0 handles mail for org1
        self.assertEquals(set(Profile.objects.mail_filter(mod0)),
                set([member0.profile, member1.profile]))
        self.assertEquals(set(Profile.objects.mail_filter(mod1)),
                set([member1.profile]))
