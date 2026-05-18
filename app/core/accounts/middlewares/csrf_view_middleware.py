from django.middleware.csrf import CsrfViewMiddleware as DjCsrfViewMiddleware


class CsrfViewMiddleware(DjCsrfViewMiddleware):
    def process_view(self, request, callback, callback_args, callback_kwargs):
        if 'json' in request.META.get('HTTP_ACCEPT', ''):  # ajax request
            origin = request.META.get('HTTP_ORIGIN')
            if origin and origin in request.META.get('HTTP_REFERER', ''):
                self._accept(request)  # ingore

        return super(CsrfViewMiddleware, self).process_view(request, callback, callback_args, callback_kwargs)
