from rest_framework import status

from core.accounts.tests.api.base_user_test import BaseUserTest
from core.projects.factories.project import ProjectFactory
from core.projects.models import Project


class ProjectApiTests(BaseUserTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.project_1 = ProjectFactory(name='Dự án bảo tồn di sản', created_by=cls.user, updated_by=cls.user)
        cls.project_2 = ProjectFactory(name='Triển lãm ảnh đời sống', created_by=cls.user, updated_by=cls.user)
        cls.project_3 = ProjectFactory(name='Sự kiện văn hóa đã xóa', created_by=cls.user, updated_by=cls.user)
        cls.project_3.delete()

    def test_list_projects(self):
        response = self.client.get('/api/projects/projects/')

        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.data['counts']['all'], 2)
        self.assertEqual(response.data['counts']['published'], 2)
        self.assertEqual(response.data['counts']['deleted'], 1)
        self.assertEqual(len(response.data['results']), 2)

    def test_search_projects(self):
        response = self.client.get('/api/projects/projects/?search=ảnh')

        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Triển lãm ảnh đời sống')

    def test_filter_deleted_projects(self):
        response = self.client.get('/api/projects/projects/?status=deleted')

        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertFalse(response.data['results'][0]['active'])

    def test_create_project(self):
        response = self.client.post(
            '/api/projects/projects/',
            {
                'website_card_title': 'Dự án mới',
                'website_card_content': 'Nội dung thẻ website',
                'hero_title': 'Hero dự án mới',
                'hero_content': 'Giới thiệu ngắn cho hero',
                'features': [
                    {
                        'icon_label': 'Biểu tượng 1',
                        'title': 'Thuyết minh di tích',
                        'description': 'Nội dung ngắn cho tính năng nổi bật.',
                    },
                ],
                'cta_title': 'Xây dựng website cao cấp',
                'cta_content': 'Chuyển mình số hóa với giao diện chuyên nghiệp.',
                'cta_button_label': 'Đăng ký tư vấn',
                'cta_button_url': 'https://example.com/tu-van',
                'long_description_title': 'Giới thiệu',
                'long_description': 'Nội dung mô tả dài cho dự án.',
                'accordion_title': 'Tư vấn tổng thể UX/UI',
                'accordion_items': [
                    {
                        'title': 'Tư vấn tổng thể UX/UI',
                        'content': 'Nội dung accordion số 1.',
                    },
                ],
            },
            format='json',
        )

        self.assertResponseStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Dự án mới')
        self.assertEqual(response.data['website_card_title'], 'Dự án mới')
        self.assertEqual(response.data['features'][0]['title'], 'Thuyết minh di tích')
        self.assertTrue(Project.objects.filter(name='Dự án mới').exists())

    def test_toggle_visibility(self):
        response = self.client.post(f'/api/projects/projects/{self.project_1.id}/toggle_visibility/')

        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.project_1.refresh_from_db()
        self.assertFalse(self.project_1.is_visible)

    def test_update_project(self):
        response = self.client.patch(
            f'/api/projects/projects/{self.project_1.id}/',
            {
                'website_card_title': 'Dự án bảo tồn di sản đã cập nhật',
                'hero_title': 'Hero mới',
                'hero_content': 'Nội dung hero mới',
                'features': [
                    {
                        'icon_label': 'Biểu tượng mới',
                        'title': 'Tính năng đã cập nhật',
                        'description': 'Mô tả đã cập nhật.',
                    },
                ],
                'accordion_items': [
                    {
                        'title': 'Accordion mới',
                        'content': 'Nội dung accordion mới.',
                    },
                ],
            },
            format='json',
        )

        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.project_1.refresh_from_db()
        self.assertEqual(self.project_1.name, 'Dự án bảo tồn di sản đã cập nhật')
        self.assertEqual(self.project_1.hero_title, 'Hero mới')
        self.assertEqual(self.project_1.features[0]['title'], 'Tính năng đã cập nhật')

    def test_hard_delete_project(self):
        response = self.client.delete(f'/api/projects/projects/{self.project_2.id}/')

        self.assertResponseStatus(response, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Project.all_objects.filter(pk=self.project_2.id).exists())