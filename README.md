# Ukrposhta International Shipping / Міжнародні відправлення Укрпошта

**EN:** Web application for creating and managing international shipments via Ukrposhta API
**UA:** Веб-додаток для створення та управління міжнародними відправленнями через API Укрпошти

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## Description / Опис

### English

**Ukrposhta International Shipping** is a ready-to-use web application for automating international shipments through the official Ukrposhta eCom API. The application provides a user-friendly interface for creating shipments, generating customs declarations (CN22, CN23), printing address labels, and tracking parcels.

**Keywords:** Ukrposhta API, international shipping Ukraine, eCom API, CN22 label, CN23 customs declaration, parcel tracking, PRIME shipment, EMS Ukraine, shipping automation, Ukrposhta integration

### Українська

**Міжнародні відправлення Укрпошта** — це готовий веб-додаток для автоматизації міжнародних відправлень через офіційний API Укрпошти (eCom API). Додаток надає зручний інтерфейс для створення відправлень, генерації митних декларацій (CN22, CN23), друку адресних етикеток та відстеження посилок.

**Ключові слова:** Укрпошта API, міжнародні відправлення, eCom API, етикетка CN22, митна декларація CN23, відстеження посилок, PRIME відправлення, EMS Україна, автоматизація відправлень, інтеграція Укрпошта, UKTZED коди

---

## Who Is This For? / Для кого цей додаток?

### English

This application is perfect for:

- **Online Store Owners** — Automate international shipping for your e-commerce business. No need to manually fill forms at the post office.
- **Dropshippers** — Quickly create shipments for international customers with automatic customs declarations.
- **Small Business Owners** — Send products abroad without complex logistics systems. Simple setup, immediate results.
- **Developers** — Use as a reference implementation for Ukrposhta API integration or as a base for custom solutions.
- **Freelancers & Crafters** — Sell handmade goods internationally (Etsy, eBay sellers) with professional shipping labels.
- **Individual Senders** — Anyone who regularly sends parcels abroad and wants to save time.

**Benefits:**
- Save 10-15 minutes per shipment vs manual post office forms
- Automatic HS code lookup (UKTZED database)
- PDF labels ready for printing
- Track all your shipments in one place
- Works with PRIME, PARCEL, EMS, SMALL_BAG, LETTER types

### Українська

Цей додаток ідеально підходить для:

- **Власників інтернет-магазинів** — Автоматизуйте міжнародні відправлення для вашого бізнесу. Не потрібно вручну заповнювати форми на пошті.
- **Дропшиперів** — Швидко створюйте відправлення для міжнародних клієнтів з автоматичними митними деклараціями.
- **Малого бізнесу** — Відправляйте товари за кордон без складних логістичних систем. Просте налаштування, миттєвий результат.
- **Розробників** — Використовуйте як приклад інтеграції з API Укрпошти або як базу для власних рішень.
- **Фрілансерів та майстрів** — Продавайте handmade товари за кордон (продавці Etsy, eBay) з професійними етикетками.
- **Приватних відправників** — Для всіх, хто регулярно відправляє посилки за кордон і хоче зекономити час.

**Переваги:**
- Економія 10-15 хвилин на кожному відправленні порівняно з ручним заповненням
- Автоматичний пошук кодів УКТЗЕД
- PDF етикетки готові до друку
- Відстеження всіх відправлень в одному місці
- Підтримка PRIME, PARCEL, EMS, SMALL_BAG, LETTER

---

## Features / Можливості

| English | Українська |
|---------|------------|
| Create International Shipments (PRIME, PARCEL, EMS, SMALL_BAG, LETTER) | Створення міжнародних відправлень (PRIME, PARCEL, EMS, SMALL_BAG, LETTER) |
| Live HS Code Search (UKTZED database) | Живий пошук кодів УКТЗЕД |
| PDF Label Generation (CN22, CN23, address labels) | Генерація PDF етикеток (CN22, CN23, адресні етикетки) |
| Shipment Tracking by barcode | Відстеження відправлень за штрих-кодом |
| Shipment Management (view, delete) | Управління відправленнями (перегляд, видалення) |
| Automatic price calculation | Автоматичний розрахунок вартості |

---

## Requirements / Вимоги

- Python 3.8+
- Ukrposhta API credentials (bearer tokens, counterparty token)
- Договір з Укрпоштою на доступ до API

---

## Installation / Встановлення

### 1. Clone the repository / Клонувати репозиторій
```bash
git clone https://github.com/yourusername/ukrposhta-international-shipping.git
cd ukrposhta-international-shipping
```

### 2. Create virtual environment / Створити віртуальне середовище
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Install dependencies / Встановити залежності
```bash
pip install -r requirements.txt
```

### 4. Configure API credentials / Налаштувати API

Copy `config.yaml.example` to `config.yaml`:
```bash
cp config.yaml.example config.yaml
```

Edit `config.yaml` with your Ukrposhta API credentials:
```yaml
environment: production

ukrposhta:
  production:
    base_url: "https://www.ukrposhta.ua"
    bearer_ecom: "YOUR_BEARER_ECOM_TOKEN"
    bearer_status: "YOUR_BEARER_STATUS_TOKEN"
    counterparty_token: "YOUR_COUNTERPARTY_TOKEN"
    counterparty_uuid: "YOUR_COUNTERPARTY_UUID"
```

### 5. Configure sender / Налаштувати відправника

Edit the `SENDER` section in `tracking_app.py`:
```python
SENDER = {
    "uuid": "YOUR_CLIENT_UUID",
    "addressId": YOUR_ADDRESS_ID,
    "name": "Your Name",
    "latinName": "Your Name in Latin",  # Required for USA
    # ... other fields
}
```

### 6. Run / Запустити
```bash
python tracking_app.py
```

### 7. Open in browser / Відкрити в браузері
```
http://localhost:5000
```

---

## Getting API Credentials / Отримання API ключів

### English
1. Register at [Ukrposhta Business](https://www.ukrposhta.ua/ua/biznes-klijentam)
2. Sign agreement for API access
3. Get your tokens from the manager
4. Documentation: [dev.ukrposhta.ua](https://dev.ukrposhta.ua/documentation)

### Українська
1. Зареєструйтесь на [Укрпошта для бізнесу](https://www.ukrposhta.ua/ua/biznes-klijentam)
2. Підпишіть договір на доступ до API
3. Отримайте токени від менеджера
4. Документація: [dev.ukrposhta.ua](https://dev.ukrposhta.ua/documentation)

---

## API Endpoints

| Endpoint | Method | Description / Опис |
|----------|--------|-------------------|
| `/` | GET | Main web interface / Головний інтерфейс |
| `/api/shipments` | GET | List all shipments / Список відправлень |
| `/api/shipment` | POST | Create new shipment / Створити відправлення |
| `/api/shipment/<uuid>` | GET | Get shipment details / Деталі відправлення |
| `/api/shipment/<uuid>` | DELETE | Delete shipment / Видалити відправлення |
| `/api/label/<uuid>` | GET | Download PDF label / Завантажити етикетку |
| `/api/track` | POST | Track by barcode / Відстежити за штрих-кодом |
| `/api/hs-codes` | GET | Search HS codes / Пошук кодів УКТЗЕД |
| `/api/countries` | GET | Get countries list / Список країн |

---

## Supported Shipment Types / Типи відправлень

| Type | Description | Max Weight |
|------|-------------|------------|
| PRIME | Express International / Експрес міжнародний | 30 kg |
| PARCEL | International Parcel / Міжнародна посилка | 30 kg |
| EMS | EMS Express | 30 kg |
| SMALL_BAG | Small Package / Мале відправлення | 2 kg |
| LETTER | International Letter / Міжнародний лист | 500 g |

---

## HS Codes / Коди УКТЗЕД

The application includes a database of common HS codes (UKTZED - Ukrainian customs classification).
Додаток містить базу популярних кодів УКТЗЕД для митного оформлення.

HS codes must be 10 digits / Коди повинні бути 10-значними:
- `6109100000` - T-shirts, cotton / Футболки бавовняні
- `9006590000` - Film cameras / Плівкові фотоапарати
- `8517120000` - Smartphones / Смартфони
- `9503009000` - Toys / Іграшки

Full list: [ukrstat.gov.ua](https://ukrstat.gov.ua/klasf/klasif/uktzed.htm)

---

## Shipment Lifecycle / Життєвий цикл відправлення

```
CREATED → REGISTERED → IN_TRANSIT → DELIVERED
   ↓
(can delete / можна видалити)
```

| Status | English | Українська |
|--------|---------|------------|
| CREATED | Created via API, can be deleted | Створено через API, можна видалити |
| REGISTERED | Accepted at post office | Прийнято на пошті |
| IN_TRANSIT | On the way | В дорозі |
| DELIVERED | Delivered to recipient | Доставлено отримувачу |

---

## Troubleshooting / Вирішення проблем

### "HS code not found" / "Код УКТЗЕД не знайдено"
- Use 10-digit UKTZED codes / Використовуйте 10-значні коди
- Search by product name / Шукайте за назвою товару
- Reference: [ukrstat.gov.ua](https://ukrstat.gov.ua/klasf/klasif/uktzed.htm)

### "latinName should not be empty"
- Add `latinName` field to sender / Додайте поле latinName
- Required for USA shipments / Обов'язково для відправлень в США

### "Client not found" / "Клієнта не знайдено"
- Create sender client via API first / Спочатку створіть клієнта через API
- Use the returned UUID / Використовуйте отриманий UUID

---

## License / Ліцензія

MIT License - see [LICENSE](LICENSE) file.

---

## Support / Підтримка

- GitHub Issues: [Report a bug](https://github.com/yourusername/ukrposhta-international-shipping/issues)
- Ukrposhta API Docs: [dev.ukrposhta.ua](https://dev.ukrposhta.ua/documentation)
- Ukrposhta Support / Підтримка Укрпошти: 0 800 300 545

---

## Contributing / Як долучитися

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## Acknowledgments / Подяки

- [Ukrposhta](https://www.ukrposhta.ua/) for providing the API
- [Flask](https://flask.palletsprojects.com/) web framework
