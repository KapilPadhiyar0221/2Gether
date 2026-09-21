"""The rules that must not quietly break: ownership, duplication, emptiness."""
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from accounts.models import Follow
from notifications.models import Notification
from posts.models import Comment, Like, Post


class Base(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="gather2gether!")
        self.bob = User.objects.create_user("bob", password="gather2gether!")
        self.post = Post.objects.create(author=self.alice, body="hello")

    def as_bob(self):
        self.client.login(username="bob", password="gather2gether!")

    def as_alice(self):
        self.client.login(username="alice", password="gather2gether!")


class DataRules(Base):
    def test_profile_is_created_with_the_user(self):
        self.assertTrue(hasattr(self.alice, "profile"))

    def test_a_post_cannot_be_completely_empty(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Post.objects.create(author=self.alice, body="")

    def test_a_person_can_only_like_a_post_once(self):
        Like.objects.create(user=self.bob, post=self.post)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Like.objects.create(user=self.bob, post=self.post)

    def test_a_follow_edge_cannot_be_duplicated(self):
        Follow.objects.create(follower=self.bob, following=self.alice)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Follow.objects.create(follower=self.bob, following=self.alice)

    def test_nobody_can_follow_themselves_in_the_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Follow.objects.create(follower=self.bob, following=self.bob)


class Authorization(Base):
    def test_anonymous_visitors_are_sent_to_sign_in(self):
        response = self.client.get(reverse("posts:home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/signin/", response.url)

    def test_you_cannot_delete_someone_elses_post(self):
        self.as_bob()
        response = self.client.post(reverse("posts:delete", args=[self.post.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    def test_the_author_can_delete_their_own_post(self):
        self.as_alice()
        self.client.post(reverse("posts:delete", args=[self.post.pk]))
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())

    def test_a_third_party_cannot_delete_a_comment(self):
        carol = User.objects.create_user("carol", password="gather2gether!")
        comment = Comment.objects.create(post=self.post, author=self.bob, body="hi")
        self.client.login(username="carol", password="gather2gether!")
        response = self.client.post(reverse("posts:delete_comment", args=[comment.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())
        carol.delete()

    def test_the_post_author_can_moderate_comments_on_their_post(self):
        comment = Comment.objects.create(post=self.post, author=self.bob, body="hi")
        self.as_alice()
        self.client.post(reverse("posts:delete_comment", args=[comment.pk]))
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_likes_and_follows_reject_GET(self):
        self.as_bob()
        self.assertEqual(self.client.get(reverse("posts:like", args=[self.post.pk])).status_code, 405)
        self.assertEqual(self.client.get(reverse("accounts:follow", args=["alice"])).status_code, 405)


class Interactions(Base):
    def test_liking_twice_toggles_off_and_notifies_once(self):
        self.as_bob()
        url = reverse("posts:like", args=[self.post.pk])

        first = self.client.post(url).json()
        self.assertTrue(first["liked"])
        self.assertEqual(first["count"], 1)
        self.assertEqual(Notification.objects.filter(verb="like").count(), 1)

        second = self.client.post(url).json()
        self.assertFalse(second["liked"])
        self.assertEqual(second["count"], 0)
        self.assertEqual(Notification.objects.filter(verb="like").count(), 0)

    def test_you_are_not_notified_about_your_own_actions(self):
        self.as_alice()
        self.client.post(reverse("posts:like", args=[self.post.pk]))
        self.assertEqual(Notification.objects.count(), 0)

    def test_following_yourself_is_rejected_by_the_view(self):
        self.as_alice()
        response = self.client.post(reverse("accounts:follow", args=["alice"]))
        self.assertEqual(response.status_code, 400)

    def test_the_home_feed_shows_people_you_follow_and_nobody_else(self):
        carol = User.objects.create_user("carol", password="x")
        Post.objects.create(author=carol, body="unfollowed noise")
        Follow.objects.create(follower=self.bob, following=self.alice)

        self.as_bob()
        body = self.client.get(reverse("posts:home")).content.decode()
        self.assertIn("hello", body)
        self.assertNotIn("unfollowed noise", body)

    def test_search_matches_handles_and_bios(self):
        self.alice.profile.bio = "ceramics and long walks"
        self.alice.profile.save()
        self.as_bob()
        self.assertIn("alice", self.client.get(reverse("accounts:search"), {"q": "ceramics"}).content.decode())
        self.assertIn("alice", self.client.get(reverse("accounts:search"), {"q": "ALI"}).content.decode())

    def test_comment_creation_returns_a_rendered_comment(self):
        self.as_bob()
        response = self.client.post(
            reverse("posts:add_comment", args=[self.post.pk]),
            {"body": "nice one"},
            headers={"x-requested-with": "fetch"},
        )
        data = response.json()
        self.assertEqual(data["count"], 1)
        self.assertIn("nice one", data["html"])

    def test_a_blank_comment_is_refused(self):
        self.as_bob()
        response = self.client.post(
            reverse("posts:add_comment", args=[self.post.pk]), {"body": "   "}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Comment.objects.count(), 0)
