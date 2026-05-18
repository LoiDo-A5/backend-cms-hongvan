def wrap_json_for_debug_toolbar(get_response):  # pragma: nocover
    from debug_toolbar.middleware import get_show_toolbar

    def middleware(request):
        response = get_response(request)

        if request.path.startswith('/__debug__/'):
            return response

        show_toolbar = get_show_toolbar()

        if show_toolbar(request):
            content = response.content.decode(response.charset)
            response.content = f'<body><pre>{content}</pre></body>'
            response.status_code = 200
            response['Content-Type'] = 'text/html'
        return response

    return middleware
