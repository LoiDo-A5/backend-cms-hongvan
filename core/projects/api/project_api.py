from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import FormParser
from rest_framework.parsers import JSONParser
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.projects.models import Project
from core.projects.serializers import ProjectListResponseSerializer
from core.projects.serializers import ProjectListSerializer
from core.projects.serializers import ProjectPublicCardSerializer
from core.projects.serializers import ProjectPublicDetailSerializer
from core.projects.serializers import ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_serializer_class(self):
        if self.action == 'public_detail':
            return ProjectPublicDetailSerializer
        if self.action == 'public_cards':
            return ProjectPublicCardSerializer
        if self.action == 'list':
            return ProjectListSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action in {'public_cards', 'public_detail'}:
            return [AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        queryset = Project.objects.all()
        search = self.request.query_params.get('search', '').strip()
        status_filter = self.request.query_params.get('status', 'all').strip().lower()

        if search:
            queryset = queryset.filter(name__icontains=search)

        if status_filter == 'deleted':
            queryset = Project.all_objects.filter(active=False)

            if search:
                queryset = queryset.filter(name__icontains=search)

        return queryset.order_by('-updated_at', '-id')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = ProjectListSerializer(queryset, many=True)
        response_serializer = ProjectListResponseSerializer(
            instance={
                'counts': {
                    'all': Project.objects.count(),
                    'published': Project.objects.count(),
                    'deleted': Project.all_objects.filter(active=False).count(),
                },
                'results': serializer.data,
            },
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'])
    def public_cards(self, request, *args, **kwargs):
        queryset = Project.objects.filter(is_visible=True).order_by('-updated_at', '-id')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def public_detail(self, request, *args, **kwargs):
        project = get_object_or_404(Project.objects.filter(is_visible=True), pk=kwargs['pk'])
        serializer = self.get_serializer(project)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        project.delete(hard=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['POST'])
    def toggle_visibility(self, request, *args, **kwargs):
        project = self.get_object()
        project.is_visible = not project.is_visible
        project.updated_by = request.user
        project.save()

        serializer = self.get_serializer(project)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def restore(self, request, *args, **kwargs):
        project = self.get_object()
        project.active = True
        project.updated_by = request.user
        project.save()

        serializer = self.get_serializer(project)
        return Response(serializer.data, status=status.HTTP_200_OK)