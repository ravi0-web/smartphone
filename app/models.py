from django.db import models
from django.utils.text import slugify

# Create your models here.
class User(models.Model):
    name=models.CharField(max_length=122)
    email=models.CharField(max_length=122)
    password=models.CharField(max_length=122)
    confirm_password=models.CharField(max_length=122)



class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.email}"


class Smartphone(models.Model):
    name = models.CharField(max_length=200, help_text="Brand name (e.g. Apple, Samsung)")
    model = models.CharField(max_length=300, help_text="Model name (e.g. iPhone 14 Pro Max)")
    slug = models.SlugField(max_length=350, unique=True, blank=True)
    display_resolution = models.CharField(max_length=200, blank=True, default='')
    os = models.CharField("Operating System", max_length=200, blank=True, default='')
    processor = models.CharField(max_length=300, blank=True, default='')
    chipset = models.CharField(max_length=300, blank=True, default='')
    gpu = models.CharField("GPU", max_length=300, blank=True, default='')
    memory = models.CharField(max_length=200, blank=True, default='')
    storage = models.CharField(max_length=200, blank=True, default='', help_text="e.g. 128 GB")
    ram = models.CharField(max_length=200, blank=True, default='', help_text="e.g. 6 GB")
    primary_camera = models.CharField(max_length=500, blank=True, default='')
    secondary_camera = models.CharField(max_length=500, blank=True, default='')
    loud_speaker = models.CharField(max_length=200, blank=True, default='')
    audio_jack = models.CharField(max_length=200, blank=True, default='')
    sensors = models.TextField(blank=True, default='')
    battery = models.CharField(max_length=300, blank=True, default='')
    colors = models.CharField(max_length=500, blank=True, default='')
    price = models.CharField(max_length=100, blank=True, default='', help_text="e.g. ₹79,900")
    img_url = models.URLField(max_length=1000, blank=True, default='')

    # Admin-controlled flags for home page sections
    is_latest = models.BooleanField("Latest Phone", default=False, help_text="Show in 'Latest Phones' section on home page")
    is_best_seller = models.BooleanField("Best Seller", default=False, help_text="Show in 'Best Selling Phones' section on home page")

    class Meta:
        ordering = ['name', 'model']
        verbose_name = 'Smartphone'
        verbose_name_plural = 'Smartphones'

    def __str__(self):
        return f"{self.name} {self.model}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.model)
            slug = base_slug
            counter = 1
            while Smartphone.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f"{self.name} {self.model}".lower()

    @property
    def ram_gb(self):
        """Extract numeric RAM value."""
        import re
        match = re.search(r'(\d+)', str(self.ram))
        return float(match.group(1)) if match else 0

    @property
    def storage_gb(self):
        """Extract numeric storage value."""
        import re
        match = re.search(r'(\d+)', str(self.storage))
        return float(match.group(1)) if match else 0

    @property
    def price_inr(self):
        """Extract numeric price value."""
        try:
            return float(str(self.price).replace('₹', '').replace(',', '').strip())
        except (ValueError, AttributeError):
            return 0