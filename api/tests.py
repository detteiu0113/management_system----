from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import CustomUser

class LoginTests(APITestCase):
    def setUp(self):
        # テストユーザーの作成
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword',
            email='testuser@example.com'
        )

    def test_login_success(self):
        # 正しい資格情報でのログインテスト
        url = reverse('login')
        data = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        response = self.client.post(url, data, format='json')
        
        # ステータスコードが200であることを確認
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # レスポンスにトークンが含まれていることを確認
        self.assertIn('refresh', response.data)
        self.assertIn('access', response.data)

    def test_login_fail_invalid_username(self):
        # 無効なユーザー名でのログインテスト
        url = reverse('login')
        data = {
            'username': 'invaliduser',
            'password': 'testpassword'
        }
        response = self.client.post(url, data, format='json')
        
        # ステータスコードが400であることを確認
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # エラーメッセージを確認
        self.assertEqual(response.data['non_field_errors'][0], '無効なユーザー名またはパスワードです。')

    def test_login_fail_invalid_password(self):
        # 無効なパスワードでのログインテスト
        url = reverse('login')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        
        # ステータスコードが400であることを確認
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # エラーメッセージを確認
        self.assertEqual(response.data['non_field_errors'][0], '無効なユーザー名またはパスワードです。')

    def test_login_no_credentials(self):
        # 資格情報なしでのログインテスト
        url = reverse('login')
        response = self.client.post(url, {}, format='json')
        
        # ステータスコードが400であることを確認
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
