from enhydris.hfaq.models import Topic, Item
from django.contrib import admin

class ItemInline(admin.TabularInline):
    model = Item
    extra = 1
    fields = ('order', 'question', 'answer', 'published', )

class TopicAdmin(admin.ModelAdmin):
    inlines = [ItemInline,]
    list_display = ('id', 'name', 'slug', 'order')
    
class ItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'order')

admin.site.register(Item, ItemAdmin)
admin.site.register(Topic, TopicAdmin)
