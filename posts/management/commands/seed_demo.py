"""Fill a fresh database with believable content so the UI can be judged.

Images are generated locally — no network, no stock photos, no licences.
"""
import io
import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFilter

from accounts.models import Follow
from notifications.models import Notification
from posts.models import Comment, Like, Post

PEOPLE = [
    ("mira", "Mira Adeyemi", "Bakes on Sundays. Argues about typography the rest of the week.", "Lagos"),
    ("tomas", "Tomás Herrera", "Bouldering, bad coffee, long walks with no destination.", "Lisbon"),
    ("anjali", "Anjali Rao", "Ceramics studio in a converted garage. Ask me about glazes.", "Pune"),
    ("kenji", "Kenji Watanabe", "Film photography. Mostly out of focus, mostly on purpose.", "Osaka"),
    ("noor", "Noor Haddad", "Urban gardener. Currently losing to the aphids.", "Amman"),
    ("erin", "Erin Doyle", "Writes at night, regrets it at 7am.", "Galway"),
]

POSTS = [
    "Third attempt at sourdough this month. The crumb finally looks like bread instead of a science fair.",
    "Walked the long way home and found a bookshop that's been there twenty years. How.",
    "Unpopular opinion: the best part of a film is the ten minutes after it ends, before anyone speaks.",
    "Kiln opened. Two survived, one cracked clean down the side. Still counting it as a good week.",
    "Started keeping a notebook of overheard sentences. Today's: \"he owns four kettles, Deborah.\"",
    "The tomatoes made it. After everything, the tomatoes made it.",
    "Rearranged the whole flat at 1am. Cannot explain it. Do not regret it.",
    "Six rolls developed, four usable frames. That ratio feels about right for life generally.",
    "Someone left a hand-drawn map taped to the bus stop. No explanation. Best thing I've seen all month.",
    "Fixed the wobbly table leg that's annoyed me since March. Genuinely the highlight of my day.",
    "New rule: if I can't explain the idea to someone in one sentence, it isn't ready yet.",
    "It rained the entire walk and I have never been in a better mood.",
]

COMMENTS = [
    "This is exactly it.",
    "Okay the crumb is genuinely beautiful.",
    "Sending this to my sister immediately.",
    "Which bookshop? Asking for me.",
    "Four kettles is an entire personality.",
    "Congratulations to the tomatoes.",
    "I needed to read this today.",
    "Post the photos, don't be shy.",
]

PALETTES = [
    ((14, 61, 48), (86, 160, 120)),
    ((38, 48, 70), (128, 150, 190)),
    ((72, 46, 32), (188, 142, 96)),
    ((30, 56, 60), (110, 168, 160)),
    ((58, 40, 54), (168, 124, 150)),
]


def make_image(seed, size=(1200, 900)):
    """A soft abstract field — stands in for a photo without pretending to be one."""
    rng = random.Random(seed)
    dark, light = rng.choice(PALETTES)
    img = Image.new("RGB", (60, 45), dark)
    draw = ImageDraw.Draw(img)
    for _ in range(7):
        x, y = rng.randint(-10, 60), rng.randint(-10, 45)
        r = rng.randint(10, 30)
        blend = rng.random()
        colour = tuple(int(dark[i] + (light[i] - dark[i]) * blend) for i in range(3))
        draw.ellipse((x - r, y - r, x + r, y + r), fill=colour)
    img = img.resize(size, Image.BICUBIC).filter(ImageFilter.GaussianBlur(14))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=84)
    return buffer.getvalue(), size[0], size[1]


def make_avatar(seed):
    data, _, _ = make_image(seed, size=(400, 400))
    return data


class Command(BaseCommand):
    help = "Create demo people, posts, likes, comments, follows and notifications."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete demo data first.")

    def handle(self, *args, **options):
        rng = random.Random(7)

        if options["reset"]:
            User.objects.filter(username__in=[p[0] for p in PEOPLE]).delete()
            self.stdout.write("Removed previous demo data.")

        users = []
        for i, (username, name, bio, city) in enumerate(PEOPLE):
            user, created = User.objects.get_or_create(
                username=username, defaults={"email": f"{username}@example.com"}
            )
            if created:
                user.set_password("gather2gether")
                user.save()
            profile = user.profile
            profile.display_name = name
            profile.bio = bio
            profile.location = city
            if i % 2 == 0:
                profile.website = f"https://{username}.example.com"
            if not profile.avatar:
                profile.avatar.save(f"{username}.jpg", ContentFile(make_avatar(username)), save=False)
            profile.save()
            users.append(user)

        # Follows: a connected-but-not-complete graph.
        for follower in users:
            for target in rng.sample(users, k=rng.randint(2, 4)):
                if target != follower:
                    Follow.objects.get_or_create(follower=follower, following=target)

        # Posts, spread over the last ten days.
        now = timezone.now()
        created_posts = []
        for i, text in enumerate(POSTS):
            author = users[i % len(users)]
            post = Post.objects.create(author=author, body=text)
            if i % 3 != 1:
                data, w, h = make_image(f"post{i}")
                post.image.save(f"demo-{i}.jpg", ContentFile(data), save=False)
                post.image_width, post.image_height = w, h
            Post.objects.filter(pk=post.pk).update(
                created_at=now - timedelta(hours=rng.randint(1, 230))
            )
            post.refresh_from_db()
            post.save(update_fields=["image", "image_width", "image_height"])
            created_posts.append(post)

        # Likes and comments, with the notifications they'd really produce.
        for post in created_posts:
            for liker in rng.sample(users, k=rng.randint(0, len(users) - 1)):
                if liker == post.author:
                    continue
                _, made = Like.objects.get_or_create(user=liker, post=post)
                if made:
                    Notification.push(post.author, liker, Notification.Verb.LIKE, post=post)
            for commenter in rng.sample(users, k=rng.randint(0, 2)):
                if commenter == post.author:
                    continue
                comment = Comment.objects.create(
                    post=post, author=commenter, body=rng.choice(COMMENTS)
                )
                Notification.push(post.author, commenter, Notification.Verb.COMMENT,
                                  post=post, comment=comment)

        for edge in Follow.objects.all()[:14]:
            Notification.push(edge.following, edge.follower, Notification.Verb.FOLLOW)

        # Leave a few unread so the badge has something to show.
        Notification.objects.update(is_read=True)
        for note in Notification.objects.all()[:5]:
            note.is_read = False
            note.save(update_fields=["is_read"])

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(users)} people, {len(created_posts)} posts. "
            f"Sign in as any handle above with the password: gather2gether"
        ))
