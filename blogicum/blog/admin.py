from django.contrib import admin
from .models import Category, Location, Post, Comment


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_published', 'created_at')
    list_editable = ('is_published',)
    list_filter = ('is_published',)
    search_fields = ('title',)
    prepopulated_fields = {'slug': ('title',)}


class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_published', 'created_at')
    list_editable = ('is_published',)
    list_filter = ('is_published',)
    search_fields = ('name',)


class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'location', 'is_published', 'pub_date')
    list_editable = ('is_published', 'category')
    list_filter = ('is_published', 'category', 'author', 'location')
    search_fields = ('title', 'text')
    date_hierarchy = 'pub_date'


class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'short_text', 'created_at')
    list_filter = ('created_at', 'author', 'post')
    search_fields = ('text', 'author__username', 'post__title')
    readonly_fields = ('created_at',)
    list_per_page = 20
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Основная информация', {
            'fields': ('post', 'author', 'created_at')
        }),
        ('Содержание', {
            'fields': ('text',),
            'classes': ('wide',)
        }),
    )
    
    def short_text(self, obj):
        if len(obj.text) > 100:
            return f"{obj.text[:100]}..."
        return obj.text
    short_text.short_description = 'Текст комментария'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.author = request.user
        super().save_model(request, obj, form, change)

admin.site.register(Category, CategoryAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)