from django.contrib import admin
from app.models import User, ContactMessage, Smartphone


admin.site.register(User)
admin.site.register(ContactMessage)


@admin.register(Smartphone)
class SmartphoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'model', 'ram', 'storage', 'price', 'is_latest', 'is_best_seller')
    list_display_links = ('name', 'model')
    list_editable = ('is_latest', 'is_best_seller')
    search_fields = ('name', 'model', 'processor', 'chipset', 'os')
    list_filter = ('name', 'os', 'is_latest', 'is_best_seller')
    list_per_page = 25
    prepopulated_fields = {'slug': ('model',)}
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'model', 'slug', 'price', 'img_url', 'colors', 'is_latest', 'is_best_seller')
        }),
        ('Display & OS', {
            'fields': ('display_resolution', 'os')
        }),
        ('Performance', {
            'fields': ('processor', 'chipset', 'gpu', 'memory', 'ram', 'storage')
        }),
        ('Camera', {
            'fields': ('primary_camera', 'secondary_camera')
        }),
        ('Audio & Sensors', {
            'fields': ('loud_speaker', 'audio_jack', 'sensors')
        }),
        ('Battery', {
            'fields': ('battery',)
        }),
    )