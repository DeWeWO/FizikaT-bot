import aiohttp
import httpx
import asyncio
import logging
from typing import Dict, List, Optional, Any
from aiohttp import ClientTimeout, ClientError
from data import config

logger = logging.getLogger(__name__)


class APIClient:
    def __init__(self):
        self.base_url = config.API_BASE_URL.rstrip("/")
        self.timeout = ClientTimeout(total=30, connect=10)
        self.session = None

    async def __aenter__(self):
        """Context manager uchun"""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager uchun"""
        if self.session:
            await self.session.close()

    async def request(self, method: str, endpoint: str, return_html=False, **kwargs) -> Optional[Dict[str, Any]]:
        """API ga umumiy so'rov yuborish"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Headers qo'shish
        headers = kwargs.get('headers', {})
        if not return_html and 'Accept' not in headers:
            headers.setdefault('Content-Type', 'application/json')
        kwargs['headers'] = headers

        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self.session is None:
                    # Agar context manager ishlatilmagan bo'lsa
                    async with aiohttp.ClientSession(timeout=self.timeout) as session:
                        async with session.request(method, url, **kwargs) as resp:
                            return await self._handle_response(resp, return_html)
                else:
                    # Context manager ishlatilgan bo'lsa
                    async with self.session.request(method, url, **kwargs) as resp:
                        return await self._handle_response(resp, return_html)

            except (ClientError, asyncio.TimeoutError):
                if attempt == max_retries - 1:
                    return None
                await asyncio.sleep(1)

            except Exception:
                return None

    async def _handle_response(self, resp, return_html=False) -> Optional[Dict[str, Any]]:
        """Response ni qayta ishlash"""
        try:
            if resp.status == 204:  # No Content
                return {"success": True}
            
            if 200 <= resp.status < 300:
                if return_html:
                    return await resp.text()
                else:
                    content_type = resp.headers.get('Content-Type', '')
                    if 'application/json' in content_type:
                        return await resp.json()
                    else:
                        return {"data": await resp.text()}
            else:
                return None
                
        except Exception:
            return None
    
    async def add_group(self, group_id: int, group_name: str) -> Optional[Dict]:
        """Guruh ma'lumotlarini Django API ga yuborish"""
        payload = {
            "group_id": group_id,
            "group_name": group_name
        }
        return await self.request("POST", "telegram/group/add/", json=payload)
    
    async def select_all_group_ids(self) -> Optional[List[int]]:
        result = await self.request("GET", "telegram-groups/all-ids/")
        if not result:
            return []
        
        groups = result.get("results") if "results" in result else result
        
        return [group.get("group_id") for group in groups if group.get("group_id")]
    

    # --- REGISTER ---
    async def registered_user(self, fio: str, telegram_id: int) -> Optional[Dict]:
        """Foydalanuvchini ro'yxatga olish"""
        payload = {
            "fio": fio,
            "telegram_id": telegram_id
        }
        return await self.request("POST", "register/register_user/", json=payload)

    async def check_registration(self, telegram_id: int) -> Optional[Dict]:
        """Foydalanuvchi ro'yxatdan o'tganligini tekshirish"""
        return await self.request("GET", f"register/check_registration/?telegram_id={telegram_id}")

    async def get_registered_user(self, telegram_id: int) -> Optional[Dict]:
        """Ro'yxatdan o'tgan foydalanuvchini topish"""
        return await self.request("GET", f"register/{telegram_id}/")

    async def update_fio(self, new_fio: str, telegram_id: int) -> Optional[Dict]:
        """FIO ni yangilash"""
        payload = {"fio": new_fio}
        return await self.request("PATCH", f"register/{telegram_id}/", json=payload)

    async def select_all_custom_users(self) -> Optional[List[Dict]]:
        """Barcha CustomUser foydalanuvchilarni olish"""
        result = await self.request("GET", "custom-users/")
        return result.get('results') if result and 'results' in result else result
    
    async def create_admin_user(self, user_data: Dict) -> Optional[Dict]:
        """Telegram bot orqali admin user yaratish"""
        result = await self.request("POST", "telegram-admin-register/", data=user_data)
        return result

    async def select_all_register_users(self) -> Optional[List[Dict]]:
        """Register jadvalidagi barcha foydalanuvchilarni olish"""
        result = await self.request("GET", "register-users/")
        return result.get('results') if result and 'results' in result else result

    async def delete_registered_user(self, telegram_id: int) -> bool:
        """Ro'yxatdan foydalanuvchini o'chirish"""
        result = await self.request("DELETE", f"register/{telegram_id}/")
        return result is not None

    # --- CATEGORIES ---
    async def get_results(self, slug: str) -> Optional[Dict]:
        """Kategoriyaga oid natijalarni olish"""
        return await self.request("GET", f"results/{slug}/")
    
    async def get_categories(self) -> Optional[List[Dict]]:
        """Barcha kategoriyalarni olish"""
        result = await self.request("GET", "categories/")
        return result.get('results') if result and 'results' in result else result

    async def get_categories_html(self) -> Optional[str]:
        """Barcha kategoriyalarni HTML sifatida olish"""
        return await self.request("GET", "api/categories/", return_html=True)

    async def get_category(self, slug: str) -> Optional[Dict]:
        """Kategoriya ma'lumotlarini olish"""
        return await self.request("GET", f"categories/{slug}/")

    async def get_category_questions(self, slug: str) -> Optional[str]:
        """Kategoriya savollarini HTML sifatida olish"""
        return await self.request("GET", f"api/categories/{slug}/questions/", return_html=True)

    # --- QUESTIONS ---
    async def get_questions(self, category_slug: str = None) -> Optional[List[Dict]]:
        """Savollarni olish"""
        if category_slug:
            result = await self.request("GET", f"questions/?category={category_slug}")
        else:
            result = await self.request("GET", "questions/")
        return result.get('results') if result and 'results' in result else result

    async def check_answers(self, category_id: int, telegram_id: int, answers: Dict[str, str]) -> Optional[str]:
        """Javoblarni tekshirish va HTML natijani qaytarish"""
        payload = {
            "category_id": category_id,
            "telegram_id": telegram_id,
            "answers": answers
        }
        return await self.request("POST", "api/questions/check_answers/?format=api", json=payload, return_html=True)

    # --- TEST RESULTS ---
    async def get_user_test_results(self, telegram_id: int) -> Optional[List[Dict]]:
        """Foydalanuvchining test natijalarini olish"""
        result = await self.request("GET", f"test-results/?telegram_id={telegram_id}")
        return result.get('results') if result and 'results' in result else result
    
    async def get_user_stats(self, telegram_id: int) -> Optional[Dict]:
        """Foydalanuvchi statistikasi"""
        return await self.request("GET", f"test-results/user_stats/?telegram_id={telegram_id}")

    # --- UTILITY METHODS ---
    async def health_check(self) -> bool:
        """API server holatini tekshirish"""
        try:
            result = await self.request("GET", "categories/")
            return result is not None
        except:
            return False

    async def close(self):
        """Session ni yopish"""
        if self.session and not self.session.closed:
            await self.session.close()

# Global instance
api_client = APIClient()