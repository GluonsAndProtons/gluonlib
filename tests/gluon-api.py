import gluonclient.api

x = api.NetworkServiceAPI('neutron', 'http://2/')

x.notify_create('123')
x.notify_delete('123')

y = api.ComputeServiceAPI('nova')

x.notify_create('456')

y.bind('456', 'myhost')
y.unbind('456')
