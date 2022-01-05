from django.http import JsonResponse
from django.template.loader import render_to_string

from posts.models import Post


def search(request):
    # This realis AJAX jqury
    # if request.is_ajax() and request.GET['data']:
    #     content = {'search_list': Post.objects.filter(
    #         text__icontains=request.GET['data']),}
    # result = render_to_string('includes/search.html', context=content)

    content = {'search_list': ''}
    data_search = request.GET['data'] or None

    if data_search:
        content = {'search_list': Post.objects.filter(
            text__icontains=data_search)}
    result = render_to_string('includes/search.html', context=content)
    return JsonResponse({'result': result})
