from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Example:
    (r'^account/', include('warara.account.urls')),
    (r'^blacklist/', include('warara.blacklist.urls')),
    (r'^board/', include('warara.board.urls')),
    (r'^message/', include('warara.message.urls')),

    # Uncomment this for admin:
#     (r'^admin/', include('django.contrib.admin.urls')),
)
