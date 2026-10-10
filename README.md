# ECO LIFE — premium ekologik platforma

Flask + SQLite asosidagi ko‘p bo‘limli ekologik maqolalar sayti.

## Lokal ishga tushirish
1. Python 3.10+ o‘rnating.
2. Terminalda loyiha papkasiga kiring.
3. `python -m venv .venv` va virtual muhitni faollashtiring.
4. `pip install -r requirements.txt`
5. `python app.py`
6. Brauzerda `http://127.0.0.1:5000` ni oching.

Birinchi ishga tushishda admin avtomatik yaratiladi:
- Email: `admin@ecolife.uz`
- Parol: `ChangeMe123!`

**Birinchi kirishdan oldin** `ADMIN_PASSWORD` va `SECRET_KEY` muhit o‘zgaruvchilarini o‘rnating yoki admin parolini almashtiring. Demo parolni ommaviy saytga qo‘ymang.

## Render orqali internetga joylash
1. GitHub’da yangi repository yarating va ushbu fayllarni yuklang.
2. Render.com’da hisob oching, **New → Blueprint** ni tanlang va repository’ni ulang.
3. `render.yaml` konfiguratsiyasini Render o‘qiydi. `ADMIN_PASSWORD` uchun kuchli, noyob parol kiriting.
4. Deploy tugagach, Render `https://...onrender.com` ko‘rinishidagi ommaviy manzil beradi.

Eslatma: hosting akkaunti va GitHub ulanishi foydalanuvchi tomonidan tasdiqlanishi kerak; loyiha fayllarini tayyorlashning o‘zi saytni avtomatik ravishda internetga joylamaydi. Doimiy SQLite saqlash uchun `render.yaml` dagi disk konfiguratsiyasi ishlatiladi; hosting tariflari va disk imkoniyatlari o‘zgarishi mumkin.

## Funksiyalar
- Premium, responsiv interfeys va animatsiyalar
- Maqolalarni qidirish va kategoriyalar bo‘yicha filtrlash
- Ro‘yxatdan o‘tish / kirish / chiqish
- Yoqtirishlar
- Admin panel orqali maqola qo‘shish va o‘chirish
- SQLite ma’lumotlar bazasi va health endpoint (`/health`)

## Xavfsizlik
Production uchun maxfiy `SECRET_KEY`, kuchli `ADMIN_PASSWORD`, HTTPS va muntazam backup ishlating. Bu boshlang‘ich loyiha; ommaviy ishga tushirishdan oldin xavfsizlik tekshiruvi va hosting konfiguratsiyasini ko‘rib chiqing.
