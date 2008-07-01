from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Example:
    # (r'^warara/', include('warara.foo.urls')),

    # Uncomment this for admin:
#     (r'^admin/', include('django.contrib.admin.urls')),
    (r'^/$', 'warara.views.intro'),    
    (r'^main/$', 'warara.views.main'),
    (r'^list/([^/]+)/$', 'warara.views.list'),
    (r'^read/([^/]+)/(\d)+/$', 'warara.views.read'),
    (r'^modify/([^/]+)/(\d)+/$', 'warara.views.modify'),
    (r'^write/([^/]+)/$', 'warara.views.write'),
    (r'^message/send/$', 'warara.views.write_message'),
    (r'^message/inbox/$', 'warara.views.inbox_list'),
    (r'^message/outbox/$', 'warara.views.outbox_list'),
    (r'^message/msu/$', 'warara.views.msu'),
    (r'^message/rim/(\d)+/$', 'warara.views.rim'),
    (r'^message/rom/(\d)+/$', 'warara.views.rom'),
)