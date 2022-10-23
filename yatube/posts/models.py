from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(unique=True, max_length=200,
                             verbose_name='название')
    slug = models.SlugField(unique=True, verbose_name='ссылка')
    description = models.TextField(verbose_name='описание')

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name='текст',
        help_text='текст поста'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата публикации'
    )
    author = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='автор'
    )
    group = models.ForeignKey(
        to=Group,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='группа',
        help_text='группа',
        blank=True,
        null=True
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = ['-pub_date']


class Comment(models.Model):
    post = models.ForeignKey(
        to=Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='пост'
    )
    author = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='автор'
    )
    text = models.TextField(
        verbose_name='текст'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата создания'
    )

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = ['-created']


class Follow(models.Model):
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='подписчик'
    )
    author = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='автор'
    )
