from django import forms

from common.images import downscale, validate_image

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("body", "image")
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "rows": 2,
                    "maxlength": 1000,
                    "placeholder": "Say something worth gathering around",
                    "aria-label": "What's on your mind",
                }
            ),
            "image": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }

    def clean_body(self):
        return self.cleaned_data.get("body", "").strip()

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image and hasattr(image, "content_type"):
            validate_image(image)
            processed, width, height = downscale(image)
            self._dimensions = (width, height)
            return processed
        return image

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("body") and not cleaned.get("image"):
            raise forms.ValidationError("Add some words or an image before posting.")
        return cleaned

    def save(self, commit=True):
        post = super().save(commit=False)
        dimensions = getattr(self, "_dimensions", None)
        if dimensions:
            post.image_width, post.image_height = dimensions
        if commit:
            post.save()
        return post


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("body",)
        widgets = {
            "body": forms.TextInput(
                attrs={"placeholder": "Add a comment", "maxlength": 500, "aria-label": "Comment"}
            )
        }

    def clean_body(self):
        body = self.cleaned_data["body"].strip()
        if not body:
            raise forms.ValidationError("Write something first.")
        return body
