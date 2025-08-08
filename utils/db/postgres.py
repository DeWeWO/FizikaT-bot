import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
from aiohttp import ClientTimeout, ClientError

from data import config


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

    # --- USERS ---
    async def add_user(self, first_name: str, last_name: str, username: str, telegram_id: int) -> Optional[Dict]:
        """Yangi foydalanuvchi qo'shish yoki mavjudini yangilash"""
        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "telegram_id": telegram_id
        }
        return await self.request("POST", "users/get_or_create_user/", json=payload)

    async def select_all_users(self) -> Optional[List[Dict]]:
        """Barcha foydalanuvchilarni olish"""
        result = await self.request("GET", "users/")
        return result.get('results') if result and 'results' in result else result

    async def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Telegram ID bo'yicha foydalanuvchi topish"""
        return await self.request("GET", f"users/{telegram_id}/")

    async def select_user(self, **kwargs) -> Optional[List[Dict]]:
        """Filtrlash orqali foydalanuvchi qidirish"""
        if not kwargs:
            return await self.select_all_users()
        
        # URL-safe params yaratish
        params = []
        for k, v in kwargs.items():
            if v is not None:
                params.append(f"{k}={v}")
        
        query_string = "&".join(params)
        result = await self.request("GET", f"users/?{query_string}")
        return result.get('results') if result and 'results' in result else result

    async def count_users(self) -> int:
        """Foydalanuvchilar sonini hisoblash"""
        result = await self.request("GET", "users/")
        if result:
            if 'count' in result:
                return result['count']
            elif 'results' in result:
                return len(result['results'])
            elif isinstance(result, list):
                return len(result)
        return 0

    async def update_user(self, telegram_id: int, **kwargs) -> Optional[Dict]:
        """Foydalanuvchi ma'lumotlarini yangilash"""
        # Faqat None bo'lmagan qiymatlarni yuborish
        payload = {k: v for k, v in kwargs.items() if v is not None}
        if payload:
            return await self.request("PATCH", f"users/{telegram_id}/", json=payload)
        return None

    async def delete_user(self, telegram_id: int) -> bool:
        """Bitta foydalanuvchini o'chirish"""
        result = await self.request("DELETE", f"users/{telegram_id}/")
        return result is not None

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

    async def delete_registered_user(self, telegram_id: int) -> bool:
        """Ro'yxatdan foydalanuvchini o'chirish"""
        result = await self.request("DELETE", f"register/{telegram_id}/")
        return result is not None

    # --- CATEGORIES ---
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