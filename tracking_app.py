"""
Web interface for tracking and creating Ukrposhta international shipments
Based on official Ukrposhta interface: ok.ukrposhta.ua
"""

from flask import Flask, render_template, request, jsonify, Response
import requests
import yaml
from datetime import datetime

app = Flask(__name__)

CONFIG_FILE = "config.yaml"


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_env_config():
    cfg = load_config()
    env = cfg["environment"]
    return cfg["ukrposhta"][env]


# ==================== TRACKING API ====================

def track_shipment(barcode: str) -> dict:
    """Get shipment statuses by barcode"""
    env_cfg = get_env_config()
    url = f"{env_cfg['base_url']}/status-tracking/0.0.1/statuses"
    headers = {
        "Authorization": f"Bearer {env_cfg['bearer_status']}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Language": "en"
    }
    params = {"barcode": barcode, "lang": "EN"}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code == 200:
            return {"success": True, "data": resp.json()}
        return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def track_multiple(barcodes: list) -> dict:
    """Track multiple shipments (up to 50)"""
    env_cfg = get_env_config()
    url = f"{env_cfg['base_url']}/status-tracking/0.0.1/statuses"
    headers = {
        "Authorization": f"Bearer {env_cfg['bearer_status']}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Language": "en"
    }
    params = {"barcode": ",".join(barcodes[:50]), "lang": "EN"}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code == 200:
            return {"success": True, "data": resp.json()}
        return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== SHIPMENT API ====================

def api_request(method: str, endpoint: str, data: dict = None, params: dict = None):
    """Make API request to Ukrposhta eCom API"""
    env_cfg = get_env_config()
    url = f"{env_cfg['base_url']}/ecom/0.0.1{endpoint}"
    headers = {
        "Authorization": f"Bearer {env_cfg['bearer_ecom']}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    if params is None:
        params = {}
    params["token"] = env_cfg["counterparty_token"]

    return requests.request(method=method, url=url, headers=headers, json=data, params=params, timeout=30)


def create_address(address_data: dict) -> dict:
    """Create address"""
    resp = api_request("POST", "/addresses", data=address_data)
    if resp.status_code == 200:
        return {"success": True, "data": resp.json()}
    return {"success": False, "error": f"{resp.status_code}: {resp.text}"}


def create_client(client_data: dict) -> dict:
    """Create client"""
    env_cfg = get_env_config()
    client_data["counterpartyUuid"] = env_cfg["counterparty_uuid"]
    resp = api_request("POST", "/clients", data=client_data)
    if resp.status_code == 200:
        return {"success": True, "data": resp.json()}
    return {"success": False, "error": f"{resp.status_code}: {resp.text}"}


def update_client(client_uuid: str, client_data: dict) -> dict:
    """Update existing client (e.g., to add latinName)"""
    env_cfg = get_env_config()
    client_data["counterpartyUuid"] = env_cfg["counterparty_uuid"]
    resp = api_request("PUT", f"/clients/{client_uuid}", data=client_data)
    if resp.status_code == 200:
        return {"success": True, "data": resp.json()}
    return {"success": False, "error": f"{resp.status_code}: {resp.text}"}


def get_client_by_uuid(client_uuid: str) -> dict:
    """Get client by UUID"""
    env_cfg = get_env_config()
    resp = api_request("GET", f"/clients/uuid/{client_uuid}")
    if resp.status_code == 200:
        return {"success": True, "data": resp.json()}
    return {"success": False, "error": f"{resp.status_code}: {resp.text}"}


def create_shipment(shipment_data: dict) -> dict:
    """Create international shipment"""
    import json
    print("\n" + "="*60)
    print("CREATE SHIPMENT REQUEST:")
    print("="*60)
    print(json.dumps(shipment_data, indent=2, ensure_ascii=False))
    print("="*60)

    resp = api_request("POST", "/shipments", data=shipment_data)

    print("\nRESPONSE STATUS:", resp.status_code)
    print("RESPONSE BODY:")
    print(resp.text[:2000] if len(resp.text) > 2000 else resp.text)
    print("="*60 + "\n")

    if resp.status_code == 200:
        return {"success": True, "data": resp.json()}
    return {"success": False, "error": f"{resp.status_code}: {resp.text}"}


def get_shipment_label(shipment_uuid: str, label_type: str = "forms") -> bytes:
    """Get shipment label PDF for international shipments

    label_type options:
    - 'forms' - combined CN22 + address label (recommended)
    - 'cn22' - customs declaration CN22
    - 'cn23' - customs declaration CN23 (for parcels > 2kg)
    - 'dl' - address label only
    """
    env_cfg = get_env_config()
    # Use /international/shipments/ path for international shipments
    url = f"{env_cfg['base_url']}/forms/ecom/0.0.1/international/shipments/{shipment_uuid}/{label_type}"
    headers = {"Authorization": f"Bearer {env_cfg['bearer_ecom']}"}
    params = {"token": env_cfg["counterparty_token"]}
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    if resp.status_code == 200:
        return resp.content
    print(f"Label error: {resp.status_code} - {resp.text[:200]}")
    return None


def delete_shipment(shipment_uuid: str) -> dict:
    """Delete shipment (only works for status CREATED)"""
    env_cfg = get_env_config()
    url = f"{env_cfg['base_url']}/ecom/0.0.1/shipments/{shipment_uuid}"
    headers = {
        "Authorization": f"Bearer {env_cfg['bearer_ecom']}",
        "Content-Type": "application/json"
    }
    params = {"token": env_cfg["counterparty_token"]}
    try:
        resp = requests.delete(url, headers=headers, params=params, timeout=30)
        if resp.status_code == 200:
            return {"success": True, "message": "Shipment deleted successfully"}
        elif resp.status_code == 400:
            return {"success": False, "error": "Cannot delete shipment. Only CREATED status can be deleted."}
        else:
            return {"success": False, "error": f"{resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_or_create_shipment_group() -> dict:
    """Get existing open group or create new one"""
    env_cfg = get_env_config()
    headers = {
        "Authorization": f"Bearer {env_cfg['bearer_ecom']}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    params = {"token": env_cfg["counterparty_token"]}

    # Create new group for today
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"{env_cfg['base_url']}/ecom/0.0.1/shipment-groups"

    try:
        resp = requests.post(url, headers=headers, params=params,
                           json={"name": f"International {today}"}, timeout=30)
        if resp.status_code == 200:
            return {"success": True, "data": resp.json()}
        return {"success": False, "error": f"{resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_all_shipment_groups() -> dict:
    """Get all shipment groups"""
    env_cfg = get_env_config()
    # This endpoint doesn't exist - groups must be tracked locally
    return {"success": False, "error": "Groups list not available via API"}


SHIPMENTS_FILE = "shipments.json"
GROUPS_FILE = "shipment_groups.json"


def load_local_data(filename: str) -> list:
    """Load data from local file"""
    import json
    import os
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []


def save_local_data(filename: str, data: list):
    """Save data to local file"""
    import json
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_shipment_locally(shipment: dict, group_uuid: str = None):
    """Save shipment to local file"""
    shipments = load_local_data(SHIPMENTS_FILE)
    shipment["group_uuid"] = group_uuid
    shipment["saved_at"] = datetime.now().isoformat()
    shipments.insert(0, shipment)
    save_local_data(SHIPMENTS_FILE, shipments[:200])


def get_shipments_list(limit: int = 50, offset: int = 0) -> dict:
    """Get list of shipments - combines local storage with API tracking"""
    shipments = load_local_data(SHIPMENTS_FILE)

    # Update status for each shipment via tracking API
    for s in shipments[:20]:  # Only update first 20 for performance
        if s.get("barcode"):
            tracking = track_shipment(s["barcode"])
            if tracking.get("success") and tracking.get("data"):
                statuses = tracking["data"]
                if isinstance(statuses, list) and len(statuses) > 0:
                    s["status"] = statuses[0].get("eventName", s.get("status"))
                    s["lastUpdate"] = statuses[0].get("date")

    return {"success": True, "data": shipments[offset:offset+limit]}


def get_shipment_by_uuid(shipment_uuid: str) -> dict:
    """Get shipment details by UUID"""
    env_cfg = get_env_config()
    url = f"{env_cfg['base_url']}/ecom/0.0.1/shipments/{shipment_uuid}"
    headers = {
        "Authorization": f"Bearer {env_cfg['bearer_ecom']}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    params = {"token": env_cfg["counterparty_token"]}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code == 200:
            return {"success": True, "data": resp.json()}
        return {"success": False, "error": f"{resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def calculate_shipping(country_code: str, weight: int, shipment_type: str = "SMALL_PACKAGE") -> dict:
    """Calculate international shipping cost using local price table"""
    # Price zones (UAH per 100g, base prices for 2026)
    # Zone 1: Europe
    # Zone 2: Americas, Asia
    # Zone 3: Other

    zone1 = ["PL", "DE", "CZ", "SK", "HU", "RO", "BG", "AT", "CH", "BE", "NL", "FR", "IT", "ES", "PT", "GB", "IE", "DK", "SE", "NO", "FI", "GR", "TR"]
    zone2 = ["US", "CA", "MX", "BR", "AR", "JP", "CN", "KR", "AU", "NZ", "SG", "MY", "TH", "VN", "IN", "IL", "AE", "PH"]

    # Base prices per zone (UAH)
    prices = {
        "SMALL_PACKAGE_PRIME": {"zone1": 280, "zone2": 380, "zone3": 420, "per100g": 25},
        "SMALL_PACKAGE": {"zone1": 220, "zone2": 320, "zone3": 360, "per100g": 20},
        "PARCEL": {"zone1": 450, "zone2": 650, "zone3": 750, "per100g": 35},
        "EMS": {"zone1": 850, "zone2": 1200, "zone3": 1400, "per100g": 55},
        "LETTER": {"zone1": 85, "zone2": 120, "zone3": 140, "per100g": 10},
        "BANDEROLE": {"zone1": 150, "zone2": 220, "zone3": 260, "per100g": 15},
    }

    # Determine zone
    if country_code in zone1:
        zone = "zone1"
    elif country_code in zone2:
        zone = "zone2"
    else:
        zone = "zone3"

    # Get price config
    price_config = prices.get(shipment_type, prices["SMALL_PACKAGE"])

    # Calculate price: base + additional per 100g above 100g
    base_price = price_config[zone]
    additional_weight = max(0, weight - 100)
    additional_price = (additional_weight // 100) * price_config["per100g"]

    total_price = base_price + additional_price

    return {"success": True, "data": {"deliveryPrice": total_price, "zone": zone, "weight": weight}}


# ==================== SENDER INFO ====================

SENDER = {
    "uuid": "YOUR_CLIENT_UUID",  # Client UUID (created via API)
    "addressId": 123456789,  # Address ID (created via API)
    "name": "Your Full Name",
    "latinName": "Your Full Name In Latin",  # Required for USA shipments
    "address": "01001, Kyiv reg., Kyiv dist., Kyiv, str. Example Street 1, apt. 1",
    "firstName": "FirstName",
    "lastName": "LastName",
    "middleName": "MiddleName",
    "phoneNumber": "380501234567",
    "tin": "1234567890",
    "postcode": "01001",
    "region": "Kyiv",
    "city": "Kyiv",
    "street": "Example Street",
    "houseNumber": "1",
    "apartmentNumber": "1",
    "country": "UA"
}


def get_or_create_sender() -> dict:
    """Get or create sender client, ensuring latinName is set for USA shipments"""
    global SENDER
    env_cfg = get_env_config()

    # Use counterparty_uuid directly from config (this is the sender's UUID)
    # This avoids the 403 error when trying to fetch sender info
    if not SENDER["uuid"]:
        SENDER["uuid"] = env_cfg["counterparty_uuid"]

    # If we already have addressId cached, return immediately
    if SENDER["uuid"] and SENDER["addressId"]:
        return {"success": True, "data": SENDER}

    # Try to get existing sender to retrieve addressId
    existing_result = get_client_by_uuid(env_cfg["counterparty_uuid"])
    if existing_result["success"]:
        existing = existing_result["data"]
        SENDER["addressId"] = existing.get("addressId")

        # Check if latinName needs to be updated
        if not existing.get("latinName") and SENDER.get("latinName"):
            print(f"Updating sender with latinName: {SENDER['latinName']}")
            update_data = {
                "latinName": SENDER["latinName"],
                "addressId": SENDER["addressId"]
            }
            update_result = update_client(SENDER["uuid"], update_data)
            if not update_result["success"]:
                print(f"Warning: Could not update sender latinName: {update_result.get('error')}")

        return {"success": True, "data": SENDER}

    # If we can't get sender info, try to create address and use it
    # This handles the case when API returns 403 for GET but might work for POST
    if not SENDER["addressId"]:
        addr_data = {
            "postcode": SENDER["postcode"],
            "country": SENDER["country"],
            "region": SENDER["region"],
            "city": SENDER["city"],
            "street": SENDER["street"],
            "houseNumber": SENDER["houseNumber"]
        }
        addr_result = create_address(addr_data)
        if addr_result["success"]:
            SENDER["addressId"] = addr_result["data"]["id"]
        else:
            # Return error but still provide UUID - shipment might work with just UUID
            print(f"Warning: Could not create address: {addr_result.get('error')}")
            # Try to continue with just the UUID
            return {"success": True, "data": SENDER, "warning": "Could not get/create address"}

    return {"success": True, "data": SENDER}


# ==================== SHIPMENT TYPES ====================

SHIPMENT_TYPES = [
    {"code": "PRIME", "name": "PRIME (Експрес міжнародний)", "maxWeight": 30000, "calcType": "PRIME", "packageType": "PRIME", "requiresTracked": True, "requiresAvia": True},
    {"code": "SMALL_BAG", "name": "Small bag (Мале відправлення)", "maxWeight": 2000, "calcType": "SMALL_PACKAGE", "packageType": "SMALL_BAG"},
    {"code": "PARCEL", "name": "Parcel (Посилка)", "maxWeight": 30000, "calcType": "PARCEL", "packageType": "PARCEL"},
    {"code": "EMS", "name": "EMS Express", "maxWeight": 30000, "calcType": "EMS", "packageType": "EMS"},
    {"code": "LETTER", "name": "Letter (Лист)", "maxWeight": 500, "calcType": "LETTER", "packageType": "LETTER"},
]

# ==================== SHIPMENT CATEGORIES ====================

SHIPMENT_CATEGORIES = [
    {"code": "GIFT", "name": "Gift (Подарунок)"},
    {"code": "SALE_OF_GOODS", "name": "Sale of goods (Продаж товарів)"},
    {"code": "COMMERCIAL_SAMPLE", "name": "Commercial sample (Комерційний зразок)"},
    {"code": "RETURNING_GOODS", "name": "Return of goods (Повернення товару)"},
    {"code": "DOCUMENTS", "name": "Documents (Документи)"},
    {"code": "MIXED_CONTENT", "name": "Mixed content (Змішаний вміст)"},
]

# ==================== HS CODES DATABASE (Common codes) ====================

HS_CODES = [
    # 10-digit UKTZED codes (Ukrainian customs classification) - REQUIRED FORMAT
    {"code": "6109100000", "description": "T-shirts, singlets, vests of cotton"},
    {"code": "6109909000", "description": "T-shirts of other textile materials"},
    {"code": "6110200000", "description": "Jerseys, pullovers, cardigans of cotton"},
    {"code": "6110309000", "description": "Jerseys, pullovers of man-made fibres"},
    {"code": "6203420000", "description": "Men's trousers of cotton"},
    {"code": "6204620000", "description": "Women's trousers of cotton"},
    {"code": "6402990000", "description": "Footwear with rubber/plastic soles"},
    {"code": "6403990000", "description": "Footwear with leather uppers"},
    {"code": "4202210000", "description": "Handbags with leather surface"},
    {"code": "4202220000", "description": "Handbags with plastic surface"},
    {"code": "4202320000", "description": "Wallets, purses of leather"},
    {"code": "7113110000", "description": "Jewelry of silver"},
    {"code": "7113190000", "description": "Jewelry of other precious metal"},
    {"code": "7117190000", "description": "Imitation jewelry"},
    {"code": "8517120000", "description": "Smartphones, mobile phones"},
    {"code": "8471300000", "description": "Laptops, portable computers"},
    {"code": "8443320000", "description": "Printers, copying machines"},
    {"code": "9102110000", "description": "Wrist-watches, electronic"},
    {"code": "9102190000", "description": "Other wrist-watches"},
    {"code": "9503009000", "description": "Toys, scale models, puzzles"},
    {"code": "9504500000", "description": "Video game consoles"},
    {"code": "4901990000", "description": "Printed books, brochures"},
    {"code": "4911100000", "description": "Advertising materials, catalogues"},
    {"code": "3304990000", "description": "Cosmetics, beauty preparations"},
    {"code": "3305100000", "description": "Shampoos"},
    {"code": "3401110000", "description": "Toilet soap"},
    {"code": "6302210000", "description": "Bed linen of cotton, printed"},
    {"code": "6302310000", "description": "Bed linen of cotton, other"},
    {"code": "8523510000", "description": "USB flash drives, memory cards"},
    {"code": "8544420000", "description": "Electric cables, conductors"},
    {"code": "6505009000", "description": "Hats, headgear knitted"},
    {"code": "6116930000", "description": "Gloves of synthetic fibres"},
    {"code": "6214200000", "description": "Shawls, scarves of wool"},
    {"code": "6217100000", "description": "Clothing accessories"},
    {"code": "4202110000", "description": "Trunks, suitcases leather"},
    {"code": "4202120000", "description": "Trunks, suitcases plastic"},
    {"code": "4202190000", "description": "Other bags, cases"},
    {"code": "9608100000", "description": "Ball point pens"},
    {"code": "9608200000", "description": "Felt pens, markers"},
    {"code": "3924900000", "description": "Household plastic articles"},
    {"code": "6912000000", "description": "Ceramic tableware"},
    {"code": "7010900000", "description": "Glass containers, jars"},
    {"code": "4823909000", "description": "Paper articles"},
    {"code": "6104430000", "description": "Women's dresses of synthetic"},
    {"code": "6106100000", "description": "Women's blouses of cotton"},
    {"code": "9006590000", "description": "Film cameras, other cameras"},
    {"code": "9006530000", "description": "Cameras for 35mm film"},
    {"code": "8525800000", "description": "Digital cameras, camcorders"},
    {"code": "9002110000", "description": "Camera lenses"},
]

# ==================== COUNTRIES ====================

COUNTRIES = [
    {"code": "US", "name": "United States", "phone": "+1"},
    {"code": "GB", "name": "United Kingdom", "phone": "+44"},
    {"code": "DE", "name": "Germany", "phone": "+49"},
    {"code": "FR", "name": "France", "phone": "+33"},
    {"code": "PL", "name": "Poland", "phone": "+48"},
    {"code": "CA", "name": "Canada", "phone": "+1"},
    {"code": "AU", "name": "Australia", "phone": "+61"},
    {"code": "PH", "name": "Philippines", "phone": "+63"},
    {"code": "JP", "name": "Japan", "phone": "+81"},
    {"code": "CN", "name": "China", "phone": "+86"},
    {"code": "IT", "name": "Italy", "phone": "+39"},
    {"code": "ES", "name": "Spain", "phone": "+34"},
    {"code": "NL", "name": "Netherlands", "phone": "+31"},
    {"code": "BE", "name": "Belgium", "phone": "+32"},
    {"code": "AT", "name": "Austria", "phone": "+43"},
    {"code": "CH", "name": "Switzerland", "phone": "+41"},
    {"code": "CZ", "name": "Czech Republic", "phone": "+420"},
    {"code": "SK", "name": "Slovakia", "phone": "+421"},
    {"code": "HU", "name": "Hungary", "phone": "+36"},
    {"code": "RO", "name": "Romania", "phone": "+40"},
    {"code": "BG", "name": "Bulgaria", "phone": "+359"},
    {"code": "TR", "name": "Turkey", "phone": "+90"},
    {"code": "IL", "name": "Israel", "phone": "+972"},
    {"code": "AE", "name": "United Arab Emirates", "phone": "+971"},
    {"code": "KR", "name": "South Korea", "phone": "+82"},
    {"code": "SG", "name": "Singapore", "phone": "+65"},
    {"code": "MY", "name": "Malaysia", "phone": "+60"},
    {"code": "TH", "name": "Thailand", "phone": "+66"},
    {"code": "VN", "name": "Vietnam", "phone": "+84"},
    {"code": "IN", "name": "India", "phone": "+91"},
    {"code": "BR", "name": "Brazil", "phone": "+55"},
    {"code": "MX", "name": "Mexico", "phone": "+52"},
    {"code": "AR", "name": "Argentina", "phone": "+54"},
    {"code": "SE", "name": "Sweden", "phone": "+46"},
    {"code": "NO", "name": "Norway", "phone": "+47"},
    {"code": "DK", "name": "Denmark", "phone": "+45"},
    {"code": "FI", "name": "Finland", "phone": "+358"},
    {"code": "PT", "name": "Portugal", "phone": "+351"},
    {"code": "GR", "name": "Greece", "phone": "+30"},
    {"code": "IE", "name": "Ireland", "phone": "+353"},
    {"code": "NZ", "name": "New Zealand", "phone": "+64"},
]

# ==================== CURRENCIES ====================

CURRENCIES = ["UAH", "USD", "EUR", "GBP"]


# ==================== HTML TEMPLATE ====================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>International postage | UKRPOSHTA</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Roboto', sans-serif;
            background: #f5f5f5;
            color: #333;
        }

        /* Header */
        .header {
            background: #fff;
            border-bottom: 1px solid #ddd;
            padding: 10px 0;
        }

        .header-container {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 20px;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 10px;
            text-decoration: none;
            color: #333;
        }

        .logo-icon {
            width: 40px;
            height: 40px;
            background: #ffcc00;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }

        .logo-text {
            font-size: 1.5rem;
            font-weight: 500;
            color: #1a5276;
        }

        .nav-tabs {
            display: flex;
            gap: 20px;
        }

        .nav-tab {
            padding: 10px 20px;
            background: none;
            border: none;
            cursor: pointer;
            font-size: 1rem;
            color: #666;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }

        .nav-tab:hover, .nav-tab.active {
            color: #1a5276;
            border-bottom-color: #ffcc00;
        }

        /* Main Container */
        .main-container {
            max-width: 1000px;
            margin: 20px auto;
            padding: 0 20px;
        }

        .page-title {
            background: #fff;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            text-align: center;
        }

        .page-title h1 {
            font-size: 1.5rem;
            font-weight: 500;
            color: #1a5276;
        }

        /* Content */
        .content {
            display: none;
            background: #fff;
            padding: 30px;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .content.active { display: block; }

        /* Tabs in content */
        .content-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 1px solid #ddd;
            padding-bottom: 10px;
        }

        .content-tab {
            padding: 10px 20px;
            background: #f5f5f5;
            border: none;
            cursor: pointer;
            border-radius: 4px 4px 0 0;
            color: #666;
            transition: all 0.3s;
        }

        .content-tab:hover, .content-tab.active {
            background: #1a5276;
            color: white;
        }

        /* Shipments table */
        .shipments-table {
            width: 100%;
            border-collapse: collapse;
        }

        .shipments-table th,
        .shipments-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }

        .shipments-table th {
            background: #f5f5f5;
            font-weight: 500;
            color: #1a5276;
        }

        .shipments-table tr:hover {
            background: #f9f9f9;
        }

        .status-badge-table {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.8rem;
        }

        .btn-icon {
            width: 32px;
            height: 32px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin: 0 2px;
        }

        .btn-icon-download {
            background: #17a2b8;
            color: white;
        }

        .btn-icon-view {
            background: #6c757d;
            color: white;
        }

        /* Form Styles */
        .form-section {
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #eee;
        }

        .form-section:last-child {
            border-bottom: none;
        }

        .section-title {
            font-size: 1.1rem;
            font-weight: 500;
            color: #1a5276;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ffcc00;
        }

        .info-box {
            background: #e8f4f8;
            border-left: 4px solid #17a2b8;
            padding: 15px;
            margin-bottom: 20px;
            font-size: 0.9rem;
        }

        .warning-box {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin-bottom: 20px;
            font-size: 0.9rem;
        }

        .form-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 15px;
        }

        .form-group {
            margin-bottom: 15px;
        }

        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
            color: #555;
        }

        .form-group label .required {
            color: #dc3545;
        }

        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }

        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #1a5276;
        }

        .form-group .input-with-addon {
            display: flex;
        }

        .form-group .input-addon {
            padding: 10px 12px;
            background: #f5f5f5;
            border: 1px solid #ccc;
            border-right: none;
            border-radius: 4px 0 0 4px;
            min-width: 60px;
        }

        .form-group .input-with-addon input {
            border-radius: 0 4px 4px 0;
        }

        .form-group .input-with-addon select {
            border-radius: 0 4px 4px 0;
            max-width: 100px;
        }

        .radio-group {
            display: flex;
            gap: 20px;
            margin-bottom: 15px;
        }

        .radio-group label {
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            font-weight: normal;
        }

        .sender-info {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }

        .sender-info p {
            margin: 5px 0;
            color: #555;
        }

        .sender-info strong {
            color: #333;
        }

        /* Attachment Card */
        .attachment-card {
            background: #f8f9fa;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 20px;
            margin-bottom: 15px;
        }

        .attachment-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .attachment-header h4 {
            color: #1a5276;
        }

        .btn-remove-attachment {
            background: #dc3545;
            color: white;
            border: none;
            padding: 5px 15px;
            border-radius: 4px;
            cursor: pointer;
        }

        /* Buttons */
        .form-actions {
            display: flex;
            gap: 15px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }

        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 4px;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s;
        }

        .btn-primary {
            background: #28a745;
            color: white;
        }

        .btn-primary:hover {
            background: #218838;
        }

        .btn-secondary {
            background: #ffc107;
            color: #333;
        }

        .btn-secondary:hover {
            background: #e0a800;
        }

        .btn-danger {
            background: #17a2b8;
            color: white;
        }

        .btn-danger:hover {
            background: #138496;
        }

        .btn-outline {
            background: white;
            border: 1px solid #1a5276;
            color: #1a5276;
        }

        .btn-outline:hover {
            background: #1a5276;
            color: white;
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        /* Tracking Results */
        .tracking-input {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }

        .tracking-input input {
            flex: 1;
            padding: 12px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: 1rem;
        }

        .shipment-card {
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 20px;
            margin-bottom: 15px;
        }

        .shipment-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #eee;
        }

        .barcode {
            font-family: monospace;
            font-size: 1.2rem;
            font-weight: bold;
            color: #1a5276;
        }

        .status-badge {
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.85rem;
        }

        .status-delivered { background: #d4edda; color: #155724; }
        .status-transit { background: #fff3cd; color: #856404; }
        .status-pending { background: #cce5ff; color: #004085; }

        .timeline {
            position: relative;
            padding-left: 30px;
        }

        .timeline::before {
            content: '';
            position: absolute;
            left: 8px;
            top: 5px;
            bottom: 5px;
            width: 2px;
            background: #ddd;
        }

        .timeline-item {
            position: relative;
            padding-bottom: 20px;
        }

        .timeline-item::before {
            content: '';
            position: absolute;
            left: -26px;
            top: 5px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #1a5276;
            border: 2px solid white;
            box-shadow: 0 0 0 2px #1a5276;
        }

        .timeline-date { font-size: 0.85rem; color: #666; }
        .timeline-status { font-weight: 500; color: #333; }
        .timeline-location { font-size: 0.9rem; color: #666; }

        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }

        .error-box {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 15px;
            border-radius: 4px;
        }

        /* Autocomplete styles for HS codes */
        .autocomplete-wrapper {
            position: relative;
        }

        .autocomplete-dropdown {
            display: none;
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #ccc;
            border-top: none;
            border-radius: 0 0 4px 4px;
            max-height: 200px;
            overflow-y: auto;
            z-index: 1000;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .autocomplete-dropdown.show {
            display: block;
        }

        .autocomplete-item {
            padding: 10px 12px;
            cursor: pointer;
            border-bottom: 1px solid #eee;
        }

        .autocomplete-item:last-child {
            border-bottom: none;
        }

        .autocomplete-item:hover {
            background: #f5f5f5;
        }

        .autocomplete-item .hs-code {
            font-weight: bold;
            color: #1a5276;
        }

        .autocomplete-item .hs-desc {
            font-size: 0.85rem;
            color: #666;
            margin-top: 2px;
        }

        .autocomplete-item .highlight {
            background: #fff3cd;
            font-weight: bold;
        }

        .hs-selected-info {
            font-size: 0.85rem;
            color: #155724;
            background: #d4edda;
            padding: 5px 10px;
            border-radius: 4px;
            margin-top: 5px;
            display: none;
        }

        .hs-selected-info.show {
            display: block;
        }

        .success-box {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 20px;
            border-radius: 4px;
        }

        .success-box h3 { margin-bottom: 15px; }
        .success-box p { margin: 5px 0; }

        .price-display {
            background: #e8f4f8;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
            font-size: 1.1rem;
        }

        .price-display strong {
            color: #1a5276;
            font-size: 1.3rem;
        }

        @media (max-width: 768px) {
            .form-row { grid-template-columns: 1fr; }
            .form-actions { flex-direction: column; }
            .nav-tabs { flex-wrap: wrap; }
        }
    </style>
</head>
<body>
    <!-- Header -->
    <header class="header">
        <div class="header-container">
            <a href="#" class="logo">
                <svg width="40" height="40" viewBox="0 0 40 40">
                    <circle cx="20" cy="20" r="18" fill="#ffcc00"/>
                    <text x="20" y="26" text-anchor="middle" font-size="14" font-weight="bold" fill="#1a5276">UP</text>
                </svg>
                <span class="logo-text">UKRPOSHTA</span>
            </a>
            <nav class="nav-tabs">
                <button class="nav-tab" onclick="showTab('shipments')">My shipments</button>
                <button class="nav-tab active" onclick="showTab('create')">Create shipment</button>
                <button class="nav-tab" onclick="showTab('track')">Track shipment</button>
            </nav>
        </div>
    </header>

    <!-- Main Content -->
    <main class="main-container">
        <div class="page-title">
            <h1>International postage</h1>
        </div>

        <!-- Shipments List Tab -->
        <div id="shipments-content" class="content">
            <div class="info-box" style="background:#fff3cd; border-color:#ffc107; color:#856404;">
                <strong>IMPORTANT INFORMATION</strong><br>
                • Shipping to the USA: Stable Delivery Times Ahead of the Holiday Season<br>
                • Find out about new international shipping rates starting January 1, 2026.<br>
                Please follow the news on the e-export portal.
            </div>

            <div class="content-tabs">
                <button class="content-tab active" onclick="showSubTab('list')">List of shipments</button>
                <button class="content-tab" onclick="showSubTab('shipment')">Shipment</button>
            </div>

            <div id="list-subtab">
                <div class="warning-box" style="margin-bottom:20px;">
                    <strong>Note:</strong> Due to Ukrposhta security policy, shipments created via personal account (ok.ukrposhta.ua)
                    are NOT accessible via API. You can import them manually by barcode below.
                </div>

                <div class="form-row" style="margin-bottom: 20px; align-items:flex-end;">
                    <div class="form-group" style="flex:2;">
                        <label>Import existing shipment by barcode:</label>
                        <div style="display:flex; gap:10px;">
                            <input type="text" id="importBarcode" placeholder="e.g. LO060405586UA" style="flex:1;">
                            <button class="btn btn-secondary" onclick="importShipment()">Import</button>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Filter by type:</label>
                        <select id="filterType" style="max-width:200px;">
                            <option value="">All shipments</option>
                        </select>
                    </div>
                </div>

                <div id="importResult" style="margin-bottom:15px;"></div>

                <div style="overflow-x:auto;">
                    <table class="shipments-table">
                        <thead>
                            <tr>
                                <th>№</th>
                                <th>Shipment number</th>
                                <th>Date</th>
                                <th>Status</th>
                                <th>Recipient name</th>
                                <th>Recipient phone</th>
                                <th>Recipient address</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="shipmentsTableBody">
                            <tr>
                                <td colspan="8" style="text-align:center; padding:40px; color:#666;">
                                    No shipments yet. Click "Create shipment" tab to add a new international shipment.
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div id="shipment-subtab" style="display:none;">
                <p style="color:#666; text-align:center; padding:40px;">
                    Select a shipment from the list to view details.
                </p>
            </div>
        </div>

        <!-- Create Shipment Tab -->
        <div id="create-content" class="content active">
            <h2 class="section-title" style="font-size:1.3rem; margin-bottom:20px;">Create shipment</h2>
            <div class="info-box" style="background:#fff3cd; border-color:#ffc107; color:#856404;">
                Dear customer, if you don't see addresses to choose from in the drop-down list, you must:
                <ul style="margin:10px 0 0 20px;">
                    <li>Go to «User profile»</li>
                    <li>Click the «Add address» button</li>
                    <li>Fill out the form that appears, correctly choose the type of shipments you plan to make (within Ukraine or international)</li>
                    <li>Save the address</li>
                    <li>Go back to creating a shipment</li>
                </ul>
            </div>

            <form id="shipmentForm" onsubmit="createShipment(event)">
                <!-- Shipment Type -->
                <div class="form-section">
                    <h3 class="section-title">Shipment Type</h3>
                    <div class="form-group">
                        <label>Select type: <span class="required">*</span></label>
                        <select name="shipmentType" id="shipmentType" required onchange="onShipmentTypeChange()">
                            <option value="">-- Select shipment type --</option>
                        </select>
                    </div>
                </div>

                <!-- Sender -->
                <div class="form-section">
                    <h3 class="section-title">Sender</h3>
                    <div class="sender-info">
                        <p><strong>SENDER_NAME</strong></p>
                        <p>Address: <strong>SENDER_ADDRESS</strong></p>
                    </div>
                    <p style="color: #17a2b8; font-size: 0.9rem;">All data must be entered with latin characters</p>
                </div>

                <!-- Recipient -->
                <div class="form-section">
                    <h3 class="section-title">Recipient</h3>

                    <div class="radio-group">
                        <label><input type="radio" name="recipientType" value="INDIVIDUAL" checked> Individual</label>
                        <label><input type="radio" name="recipientType" value="LEGAL_ENTITY"> Legal entity</label>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label>Country: <span class="required">*</span></label>
                            <select name="country" id="countrySelect" required onchange="onCountryChange()">
                                <option value="">-- Select country --</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Last name and First name: <span class="required">*</span></label>
                            <input type="text" name="fullName" placeholder="Last name and First name" required>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label>E-mail:</label>
                            <input type="email" name="email" placeholder="E-mail">
                        </div>
                        <div class="form-group">
                            <label>Phone: <span class="required">*</span></label>
                            <div class="input-with-addon">
                                <select name="phoneCode" id="phoneCode" style="width: 100px;">
                                    <option value="+1">+1</option>
                                </select>
                                <input type="tel" name="phone" placeholder="Phone number" required>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Recipient Address -->
                <div class="form-section">
                    <h3 class="section-title">Recipient address</h3>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Region/State:</label>
                            <input type="text" name="region" placeholder="Region/State">
                        </div>
                        <div class="form-group">
                            <label>Zip code:</label>
                            <input type="text" name="zipCode" placeholder="Zip code">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>City: <span class="required">*</span></label>
                            <input type="text" name="city" placeholder="City" required>
                        </div>
                        <div class="form-group">
                            <label>Address: <span class="required">*</span></label>
                            <input type="text" name="address" placeholder="Address" required>
                        </div>
                    </div>
                </div>

                <!-- Shipment Information -->
                <div class="form-section">
                    <h3 class="section-title">Information about shipment</h3>
                    <div class="info-box" id="shipmentTypeInfo">
                        Shipment type: <strong>Not selected</strong>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Gross weight, g: <span class="required">*</span></label>
                            <input type="number" name="weight" id="weightInput" min="1" max="30000" placeholder="Gross weight, g" required onchange="updatePrice()">
                        </div>
                        <div class="form-group">
                            <label>Length, cm: <span class="required">*</span></label>
                            <input type="number" name="length" min="1" value="20" placeholder="Length, cm" required>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Width, cm: <span class="required">*</span></label>
                            <input type="number" name="width" min="1" value="15" placeholder="Width, cm" required>
                        </div>
                        <div class="form-group">
                            <label>Height, cm: <span class="required">*</span></label>
                            <input type="number" name="height" min="1" value="10" placeholder="Height, cm" required>
                        </div>
                    </div>
                </div>

                <!-- Attachments -->
                <div class="form-section">
                    <h3 class="section-title">Attachment info</h3>
                    <div id="attachmentsContainer">
                        <div class="attachment-card" data-index="0">
                            <div class="attachment-header">
                                <h4>Attachment</h4>
                                <button type="button" class="btn-remove-attachment" onclick="removeAttachment(this)" style="display:none;">Delete attachment</button>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label>CNFEA code (HS Code): <span class="required">*</span></label>
                                    <div class="autocomplete-wrapper">
                                        <input type="text" name="hsCode[]" class="hs-code-input" placeholder="Enter code or name (e.g. 6109100000 or T-shirt)" required autocomplete="off">
                                        <div class="autocomplete-dropdown"></div>
                                    </div>
                                    <div class="hs-selected-info"></div>
                                </div>
                                <div class="form-group">
                                    <label>Detailed description of the attachment EN: <span class="required">*</span></label>
                                    <input type="text" name="description[]" class="hs-description" placeholder="e.g. Cotton T-Shirt" required>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Cost of attachment (for tax declaration): <span class="required">*</span></label>
                                    <div class="input-with-addon">
                                        <input type="number" name="itemCost[]" min="0" step="0.01" placeholder="Cost of attachment" required style="flex:1;">
                                        <select name="itemCurrency[]">
                                            <option value="UAH">UAH</option>
                                            <option value="USD">USD</option>
                                            <option value="EUR">EUR</option>
                                            <option value="GBP">GBP</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label>Number of units, unit: <span class="required">*</span></label>
                                    <input type="number" name="itemQty[]" min="1" value="1" placeholder="Number of units, unit" required>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Unpackaged attachment weight, g: <span class="required">*</span></label>
                                    <input type="number" name="itemWeight[]" min="1" placeholder="Unpackaged attachment weight, g" required>
                                </div>
                                <div class="form-group">
                                    <label>Attachment's country of origin: <span class="required">*</span></label>
                                    <select name="itemOrigin[]" required>
                                        <option value="UA" selected>Ukraine</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>

                    <button type="button" class="btn btn-outline" onclick="addAttachment()">Add attachment</button>

                    <div class="warning-box" style="margin-top: 20px;">
                        According to the changes in the customs legislation of Ukraine, aimed at compliance with world standards, the "HS Code" field
                        is mandatory. We are already asking you to independently define and specify the
                        commodity code of the attachment (at least 6 digits without punctuation marks and spaces) according to international
                        standards. You can use the <a href="https://www.wcoomd.org/en/topics/nomenclature/instrument-and-tools/hs-nomenclature-2022-edition.aspx" target="_blank">Harmonized System database</a>
                        by the World Customs Organization.
                    </div>
                </div>

                <!-- Customs Information -->
                <div class="form-section">
                    <h3 class="section-title">Information for customs declarations</h3>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Shipment category: <span class="required">*</span></label>
                            <select name="category" required>
                                <option value="">-- Select category --</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Information for EU customs:</label>
                            <input type="text" name="euInfo" placeholder="Additional info for EU customs">
                        </div>
                    </div>
                </div>

                <!-- Price Display -->
                <div class="price-display" id="priceDisplay" style="display:none;">
                    Estimated shipping cost: <strong id="priceValue">-</strong>
                </div>

                <!-- Actions -->
                <div class="form-actions">
                    <button type="button" class="btn btn-danger" onclick="resetForm()">Cancel</button>
                    <button type="button" class="btn btn-secondary" onclick="calculatePrice()">Calculate</button>
                    <button type="submit" class="btn btn-primary" id="submitBtn">Save</button>
                </div>
            </form>

            <div id="shipmentResult" style="margin-top: 20px;"></div>
        </div>

        <!-- Track Tab -->
        <div id="track-content" class="content">
            <h3 class="section-title">Enter tracking number</h3>
            <div class="tracking-input">
                <input type="text" id="barcodeInput" placeholder="e.g. RR123456789UA" onkeypress="if(event.key==='Enter') trackShipment()">
                <button class="btn btn-primary" onclick="trackShipment()">Track</button>
            </div>
            <p style="color: #666; font-size: 0.9rem; margin-bottom: 20px;">
                Enter one or more tracking numbers (separated by comma or space). Maximum 50 shipments.
            </p>
            <div id="trackResults"></div>
        </div>
    </main>

    <script>
        // Data from server
        const countries = COUNTRIES_JSON;
        const shipmentTypes = SHIPMENT_TYPES_JSON;
        const categories = CATEGORIES_JSON;
        const sender = SENDER_JSON;
        const hsCodes = HS_CODES_JSON;

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            // Populate shipment types
            const typeSelect = document.getElementById('shipmentType');
            const filterType = document.getElementById('filterType');
            shipmentTypes.forEach(t => {
                typeSelect.innerHTML += `<option value="${t.code}">${t.name}</option>`;
                filterType.innerHTML += `<option value="${t.code}">${t.name}</option>`;
            });

            // Use shipment types from server for filter
            filterType.innerHTML = '<option value="">All shipments</option>' +
                shipmentTypes.map(t => `<option value="${t.code}">${t.name}</option>`).join('');

            // Populate countries (sorted)
            const countrySelect = document.getElementById('countrySelect');
            const phoneCode = document.getElementById('phoneCode');
            const sorted = [...countries].sort((a,b) => a.name.localeCompare(b.name));
            sorted.forEach(c => {
                countrySelect.innerHTML += `<option value="${c.code}" data-phone="${c.phone}">${c.name}</option>`;
            });
            phoneCode.innerHTML = sorted.map(c => `<option value="${c.phone}">${c.phone}</option>`).join('');

            // Populate categories
            const catSelect = document.querySelector('select[name="category"]');
            categories.forEach(c => {
                catSelect.innerHTML += `<option value="${c.code}">${c.name}</option>`;
            });

            // Update sender info
            document.querySelector('.sender-info').innerHTML = `
                <p><strong>${sender.name}</strong></p>
                <p>Address: <strong>${sender.address}</strong></p>
            `;

            // Initialize HS code autocomplete for existing inputs
            initHsCodeAutocomplete();
        });

        // HS Code autocomplete with live search
        function initHsCodeAutocomplete() {
            document.querySelectorAll('.hs-code-input').forEach(input => {
                if (input.dataset.autocompleteInit) return;
                input.dataset.autocompleteInit = 'true';

                const wrapper = input.closest('.autocomplete-wrapper');
                const dropdown = wrapper.querySelector('.autocomplete-dropdown');
                const formGroup = input.closest('.form-group');
                const infoDiv = formGroup.querySelector('.hs-selected-info');
                const descInput = input.closest('.attachment-card').querySelector('.hs-description');

                // Highlight matching text
                function highlightMatch(text, query) {
                    const regex = new RegExp(`(${query})`, 'gi');
                    return text.replace(regex, '<span class="highlight">$1</span>');
                }

                // Update selected info display
                function updateSelectedInfo(code, desc) {
                    if (infoDiv) {
                        if (code && desc) {
                            infoDiv.innerHTML = `<strong>${code}</strong> — ${desc}`;
                            infoDiv.classList.add('show');
                        } else {
                            infoDiv.classList.remove('show');
                        }
                    }
                }

                // Check if entered value matches an HS code
                function checkExactMatch(value) {
                    const match = hsCodes.find(hs => hs.code === value);
                    if (match) {
                        updateSelectedInfo(match.code, match.description);
                        if (descInput && !descInput.value) {
                            descInput.value = match.description;
                        }
                    } else {
                        updateSelectedInfo(null, null);
                    }
                }

                input.addEventListener('input', function() {
                    const value = this.value.trim();
                    const valueLower = value.toLowerCase();

                    // Check for exact code match
                    checkExactMatch(value);

                    if (value.length < 2) {
                        dropdown.classList.remove('show');
                        return;
                    }

                    // Search by code OR description
                    const matches = hsCodes.filter(hs =>
                        hs.code.includes(value) || hs.description.toLowerCase().includes(valueLower)
                    ).slice(0, 15);

                    if (matches.length === 0) {
                        dropdown.innerHTML = '<div class="autocomplete-item" style="color:#999;">No matches found</div>';
                        dropdown.classList.add('show');
                        return;
                    }

                    dropdown.innerHTML = matches.map(hs => {
                        const codeHighlighted = highlightMatch(hs.code, value);
                        const descHighlighted = highlightMatch(hs.description, valueLower);
                        return `
                            <div class="autocomplete-item" data-code="${hs.code}" data-desc="${hs.description}">
                                <div class="hs-code">${codeHighlighted}</div>
                                <div class="hs-desc">${descHighlighted}</div>
                            </div>
                        `;
                    }).join('');

                    dropdown.querySelectorAll('.autocomplete-item[data-code]').forEach(item => {
                        item.addEventListener('click', function() {
                            const code = this.dataset.code;
                            const desc = this.dataset.desc;
                            input.value = code;
                            updateSelectedInfo(code, desc);
                            if (descInput && !descInput.value) {
                                descInput.value = desc;
                            }
                            dropdown.classList.remove('show');
                        });
                    });

                    dropdown.classList.add('show');
                });

                input.addEventListener('blur', function() {
                    setTimeout(() => {
                        dropdown.classList.remove('show');
                        checkExactMatch(this.value.trim());
                    }, 200);
                });

                input.addEventListener('focus', function() {
                    if (this.value.length >= 2) {
                        this.dispatchEvent(new Event('input'));
                    }
                });

                // Check initial value
                if (input.value) {
                    checkExactMatch(input.value.trim());
                }
            });
        }

        // Tab switching
        function showTab(tab) {
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.content').forEach(c => c.classList.remove('active'));
            document.querySelector(`.nav-tab[onclick="showTab('${tab}')"]`).classList.add('active');
            document.getElementById(`${tab}-content`).classList.add('active');
        }

        // Sub-tab switching
        function showSubTab(subtab) {
            document.querySelectorAll('.content-tab').forEach(t => t.classList.remove('active'));
            document.querySelector(`[onclick="showSubTab('${subtab}')"]`).classList.add('active');
            document.getElementById('list-subtab').style.display = subtab === 'list' ? 'block' : 'none';
            document.getElementById('shipment-subtab').style.display = subtab === 'shipment' ? 'block' : 'none';
        }

        // Sidebar navigation
        function navigateTo(section) {
            if (section === 'international') {
                showTab('shipments');
            }
        }

        // Shipments from API
        let allShipments = [];

        async function loadShipments() {
            const tbody = document.getElementById('shipmentsTableBody');
            tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:40px; color:#666;">Loading shipments...</td></tr>`;

            try {
                const resp = await fetch('/api/shipments?limit=50');
                const data = await resp.json();

                if (data.success && data.data) {
                    allShipments = Array.isArray(data.data) ? data.data : [data.data];
                    updateShipmentsTable();
                } else {
                    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:40px; color:#c00;">Error: ${data.error || 'Failed to load'}</td></tr>`;
                }
            } catch (e) {
                tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:40px; color:#c00;">Connection error: ${e.message}</td></tr>`;
            }
        }

        function updateShipmentsTable() {
            const tbody = document.getElementById('shipmentsTableBody');
            const filterValue = document.getElementById('filterType').value;

            let shipments = allShipments;
            if (filterValue) {
                shipments = shipments.filter(s => s.type === filterValue);
            }

            if (shipments.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="8" style="text-align:center; padding:40px; color:#666;">
                            No shipments found. Click "Create shipment" to add a new international shipment.
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = shipments.map((s, i) => {
                const recipient = s.recipient || {};
                const recipientAddr = s.recipientAddress || {};
                const date = s.lastModified || s.created || '';
                const formattedDate = date ? new Date(date).toLocaleString('uk-UA') : '-';

                return `
                <tr>
                    <td>${i + 1}</td>
                    <td><span class="barcode">${s.barcode || '-'}</span></td>
                    <td>${formattedDate}</td>
                    <td><span class="status-badge-table ${getStatusClass(s.status)}">${s.status || '-'}</span></td>
                    <td>${recipient.name || recipient.firstName || '-'}</td>
                    <td>${recipient.phoneNumber || '-'}</td>
                    <td>${formatAddress(recipientAddr)}</td>
                    <td>
                        <a href="/api/label/${s.uuid}" class="btn-icon btn-icon-download" target="_blank" title="Download label">📥</a>
                        <button class="btn-icon btn-icon-view" onclick="viewShipmentDetails('${s.uuid}')" title="View details">👁</button>
                        <button class="btn-icon" onclick="deleteShipment('${s.uuid}')" title="Delete shipment" style="color:#c0392b;">🗑</button>
                    </td>
                </tr>
            `}).join('');
        }

        function formatAddress(addr) {
            if (!addr) return '-';
            const parts = [addr.country, addr.city, addr.street].filter(Boolean);
            return parts.join(', ') || '-';
        }

        function getStatusClass(status) {
            if (!status) return 'status-pending';
            const s = status.toLowerCase();
            if (s.includes('deliver')) return 'status-delivered';
            if (s.includes('transit') || s.includes('send')) return 'status-transit';
            return 'status-pending';
        }

        async function viewShipmentDetails(uuid) {
            const detailsDiv = document.getElementById('shipment-subtab');
            detailsDiv.innerHTML = '<p style="text-align:center; padding:20px;">Loading...</p>';
            showSubTab('shipment');

            try {
                const resp = await fetch(`/api/shipment/${uuid}`);
                const data = await resp.json();

                if (data.success && data.data) {
                    const s = data.data;
                    const recipient = s.recipient || {};
                    const recipientAddr = s.recipientAddress || {};

                    detailsDiv.innerHTML = `
                        <div class="shipment-card">
                            <h3 style="margin-bottom:15px; color:#1a5276;">Shipment Details</h3>
                            <div class="form-row">
                                <p><strong>Barcode:</strong> <span class="barcode">${s.barcode || '-'}</span></p>
                                <p><strong>UUID:</strong> ${s.uuid || '-'}</p>
                            </div>
                            <div class="form-row">
                                <p><strong>Type:</strong> ${s.type || '-'}</p>
                                <p><strong>Status:</strong> ${s.status || '-'}</p>
                            </div>
                            <div class="form-row">
                                <p><strong>Recipient:</strong> ${recipient.name || '-'}</p>
                                <p><strong>Phone:</strong> ${recipient.phoneNumber || '-'}</p>
                            </div>
                            <div class="form-row">
                                <p><strong>Address:</strong> ${formatAddress(recipientAddr)}</p>
                            </div>
                            <div class="form-row">
                                <p><strong>Weight:</strong> ${s.weight || '-'} g</p>
                                <p><strong>Price:</strong> ${s.deliveryPrice || '-'} UAH</p>
                            </div>
                            <div style="margin-top:20px;">
                                <a href="/api/label/${s.uuid}" class="btn btn-secondary" target="_blank">Download Label (PDF)</a>
                                <button class="btn btn-outline" onclick="trackByBarcode('${s.barcode}')" style="margin-left:10px;">Track</button>
                                <button class="btn" onclick="deleteShipment('${s.uuid}')" style="margin-left:10px; background:#c0392b;">Delete</button>
                            </div>
                        </div>
                    `;
                } else {
                    detailsDiv.innerHTML = `<p style="color:#c00; padding:20px;">Error: ${data.error}</p>`;
                }
            } catch (e) {
                detailsDiv.innerHTML = `<p style="color:#c00; padding:20px;">Connection error</p>`;
            }
        }

        function trackByBarcode(barcode) {
            if (!barcode) return;
            document.getElementById('barcodeInput').value = barcode;
            showTab('track');
            trackShipment();
        }

        async function deleteShipment(uuid) {
            if (!confirm('Are you sure you want to delete this shipment?\\n\\nNote: Only shipments with status CREATED can be deleted.')) {
                return;
            }

            try {
                const resp = await fetch(`/api/shipment/${uuid}`, {
                    method: 'DELETE'
                });
                const data = await resp.json();

                if (data.success) {
                    alert('Shipment deleted successfully!');
                    loadShipments(); // Refresh the list
                } else {
                    alert('Error: ' + (data.error || 'Could not delete shipment'));
                }
            } catch (e) {
                alert('Connection error: ' + e.message);
            }
        }

        async function importShipment() {
            const barcode = document.getElementById('importBarcode').value.trim();
            const resultDiv = document.getElementById('importResult');

            if (!barcode) {
                resultDiv.innerHTML = '<div class="error-box">Please enter a barcode</div>';
                return;
            }

            resultDiv.innerHTML = '<p>Importing...</p>';

            try {
                const resp = await fetch('/api/import-shipment', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({barcode: barcode})
                });
                const data = await resp.json();

                if (data.success) {
                    resultDiv.innerHTML = `<div class="success-box">Shipment ${barcode} imported successfully! Status: ${data.data.status}</div>`;
                    document.getElementById('importBarcode').value = '';
                    loadShipments();
                } else {
                    resultDiv.innerHTML = `<div class="error-box">${data.error}</div>`;
                }
            } catch (e) {
                resultDiv.innerHTML = `<div class="error-box">Connection error</div>`;
            }
        }

        // Filter change handler
        document.getElementById('filterType')?.addEventListener('change', updateShipmentsTable);

        // Load shipments on page load
        document.addEventListener('DOMContentLoaded', loadShipments);

        // Country change
        function onCountryChange() {
            const select = document.getElementById('countrySelect');
            const option = select.options[select.selectedIndex];
            if (option && option.dataset.phone) {
                document.getElementById('phoneCode').value = option.dataset.phone;
            }
            updatePrice();
        }

        // Shipment type change
        function onShipmentTypeChange() {
            const select = document.getElementById('shipmentType');
            const type = shipmentTypes.find(t => t.code === select.value);
            if (type) {
                document.getElementById('shipmentTypeInfo').innerHTML = `Shipment type: <strong>${type.name}</strong> (max ${type.maxWeight}g)`;
                document.getElementById('weightInput').max = type.maxWeight;
            }
            updatePrice();
        }

        // Attachments
        let attachmentIndex = 1;
        function addAttachment() {
            const container = document.getElementById('attachmentsContainer');
            const card = document.createElement('div');
            card.className = 'attachment-card';
            card.dataset.index = attachmentIndex++;
            card.innerHTML = `
                <div class="attachment-header">
                    <h4>Attachment №${attachmentIndex}</h4>
                    <button type="button" class="btn-remove-attachment" onclick="removeAttachment(this)">Delete attachment</button>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>CNFEA code (HS Code): <span class="required">*</span></label>
                        <div class="autocomplete-wrapper">
                            <input type="text" name="hsCode[]" class="hs-code-input" placeholder="Enter code or name (e.g. 6109100000 or T-shirt)" required autocomplete="off">
                            <div class="autocomplete-dropdown"></div>
                        </div>
                        <div class="hs-selected-info"></div>
                    </div>
                    <div class="form-group">
                        <label>Detailed description of the attachment EN: <span class="required">*</span></label>
                        <input type="text" name="description[]" class="hs-description" placeholder="e.g. Cotton T-Shirt" required>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Cost of attachment (for tax declaration): <span class="required">*</span></label>
                        <div class="input-with-addon">
                            <input type="number" name="itemCost[]" min="0" step="0.01" placeholder="Cost of attachment" required style="flex:1;">
                            <select name="itemCurrency[]">
                                <option value="UAH">UAH</option>
                                <option value="USD">USD</option>
                                <option value="EUR">EUR</option>
                                <option value="GBP">GBP</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Number of units, unit: <span class="required">*</span></label>
                        <input type="number" name="itemQty[]" min="1" value="1" placeholder="Number of units, unit" required>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Unpackaged attachment weight, g: <span class="required">*</span></label>
                        <input type="number" name="itemWeight[]" min="1" placeholder="Unpackaged attachment weight, g" required>
                    </div>
                    <div class="form-group">
                        <label>Attachment's country of origin: <span class="required">*</span></label>
                        <select name="itemOrigin[]" required>
                            <option value="UA" selected>Ukraine</option>
                        </select>
                    </div>
                </div>
            `;
            container.appendChild(card);
            updateRemoveButtons();
            initHsCodeAutocomplete();
        }

        function removeAttachment(btn) {
            btn.closest('.attachment-card').remove();
            updateRemoveButtons();
        }

        function updateRemoveButtons() {
            const cards = document.querySelectorAll('.attachment-card');
            cards.forEach((card, i) => {
                const btn = card.querySelector('.btn-remove-attachment');
                btn.style.display = cards.length > 1 ? 'block' : 'none';
            });
        }

        // Price calculation
        async function updatePrice() {
            const country = document.getElementById('countrySelect').value;
            const weight = document.getElementById('weightInput').value;
            const type = document.getElementById('shipmentType').value;
            const priceDisplay = document.getElementById('priceDisplay');
            const priceValue = document.getElementById('priceValue');

            if (!country || !weight || !type) {
                priceDisplay.style.display = 'none';
                return;
            }

            priceValue.textContent = 'Calculating...';
            priceDisplay.style.display = 'block';
            priceDisplay.style.background = '#e8f4f8';

            try {
                const resp = await fetch(`/api/calculate?country=${country}&weight=${weight}&type=${type}`);
                const data = await resp.json();

                if (data.success && data.data) {
                    const price = data.data.deliveryPrice || data.data.price || data.data.totalPrice || data.data;
                    if (price && typeof price === 'number') {
                        priceValue.textContent = price.toFixed(2) + ' UAH';
                        priceDisplay.style.background = '#d4edda';
                    } else if (typeof price === 'object') {
                        // Try to find price in nested object
                        const foundPrice = price.deliveryPrice || price.price || price.totalPrice;
                        if (foundPrice) {
                            priceValue.textContent = foundPrice.toFixed(2) + ' UAH';
                            priceDisplay.style.background = '#d4edda';
                        } else {
                            priceValue.textContent = JSON.stringify(price);
                        }
                    } else {
                        priceValue.textContent = price + ' UAH';
                        priceDisplay.style.background = '#d4edda';
                    }
                } else {
                    priceValue.textContent = 'Error: ' + (data.error || 'Unknown error');
                    priceDisplay.style.background = '#f8d7da';
                }
            } catch (e) {
                console.error('Price error:', e);
                priceValue.textContent = 'Connection error';
                priceDisplay.style.background = '#f8d7da';
            }
        }

        function calculatePrice() {
            updatePrice();
        }

        function resetForm() {
            document.getElementById('shipmentForm').reset();
            document.getElementById('priceDisplay').style.display = 'none';
            document.getElementById('shipmentResult').innerHTML = '';
        }

        // Create shipment
        async function createShipment(event) {
            event.preventDefault();

            const form = document.getElementById('shipmentForm');
            const submitBtn = document.getElementById('submitBtn');
            const resultDiv = document.getElementById('shipmentResult');

            submitBtn.disabled = true;
            submitBtn.textContent = 'Saving...';

            const formData = new FormData(form);

            // Collect attachments
            const items = [];
            const hsCodes = formData.getAll('hsCode[]');
            const descriptions = formData.getAll('description[]');
            const costs = formData.getAll('itemCost[]');
            const currencies = formData.getAll('itemCurrency[]');
            const qtys = formData.getAll('itemQty[]');
            const weights = formData.getAll('itemWeight[]');

            for (let i = 0; i < hsCodes.length; i++) {
                items.push({
                    hsCode: hsCodes[i],
                    latinName: descriptions[i],
                    price: parseFloat(costs[i]),
                    currency: currencies[i],
                    quantity: parseInt(qtys[i]),
                    weight: parseInt(weights[i]),
                    countryOfOrigin: 'UA'
                });
            }

            const shipmentData = {
                type: formData.get('shipmentType'),
                category: formData.get('category'),
                recipient: {
                    type: formData.get('recipientType'),
                    fullName: formData.get('fullName'),
                    phone: formData.get('phoneCode') + formData.get('phone'),
                    email: formData.get('email') || null
                },
                address: {
                    country: formData.get('country'),
                    region: formData.get('region') || null,
                    zipCode: formData.get('zipCode') || null,
                    city: formData.get('city'),
                    address: formData.get('address')
                },
                package: {
                    weight: parseInt(formData.get('weight')),
                    length: parseInt(formData.get('length')),
                    width: parseInt(formData.get('width')),
                    height: parseInt(formData.get('height'))
                },
                items: items,
                euInfo: formData.get('euInfo') || null
            };

            try {
                const resp = await fetch('/api/shipment', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(shipmentData)
                });

                const data = await resp.json();

                if (data.success) {
                    const s = data.data;
                    resultDiv.innerHTML = `
                        <div class="success-box">
                            <h3>Shipment Created Successfully!</h3>
                            <p><strong>Barcode:</strong> <span class="barcode">${s.barcode || s.uuid}</span></p>
                            <p><strong>UUID:</strong> ${s.uuid}</p>
                            ${s.deliveryPrice ? `<p><strong>Price:</strong> ${s.deliveryPrice} UAH</p>` : ''}
                            <br>
                            <a href="/api/label/${s.uuid}" class="btn btn-secondary" target="_blank">Download Label (PDF)</a>
                            <button class="btn btn-outline" onclick="showTab('shipments'); loadShipments();" style="margin-left:10px;">View My Shipments</button>
                        </div>
                    `;

                    form.reset();
                    document.getElementById('priceDisplay').style.display = 'none';

                    // Reload shipments list
                    loadShipments();
                } else {
                    resultDiv.innerHTML = `<div class="error-box"><strong>Error:</strong> ${data.error}</div>`;
                }
            } catch (error) {
                resultDiv.innerHTML = `<div class="error-box"><strong>Error:</strong> ${error.message}</div>`;
            }

            submitBtn.disabled = false;
            submitBtn.textContent = 'Save';
        }

        // Tracking
        async function trackShipment() {
            const input = document.getElementById('barcodeInput').value.trim();
            if (!input) return;

            const barcodes = input.split(/[,\\s]+/).filter(b => b.length > 0);
            const resultsDiv = document.getElementById('trackResults');

            resultsDiv.innerHTML = '<div class="loading">Loading...</div>';

            try {
                const response = await fetch('/api/track', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({barcodes: barcodes})
                });

                const data = await response.json();

                if (data.success) {
                    displayResults(data.data, barcodes);
                } else {
                    resultsDiv.innerHTML = `<div class="error-box">${data.error}</div>`;
                }
            } catch (error) {
                resultsDiv.innerHTML = `<div class="error-box">Connection error: ${error.message}</div>`;
            }
        }

        function displayResults(data, barcodes) {
            const resultsDiv = document.getElementById('trackResults');

            if (!data || (Array.isArray(data) && data.length === 0)) {
                resultsDiv.innerHTML = '<p>Shipment not found</p>';
                return;
            }

            let html = '';
            const shipments = {};
            const items = Array.isArray(data) ? data : [data];

            items.forEach(status => {
                const barcode = status.barcode || 'unknown';
                if (!shipments[barcode]) shipments[barcode] = [];
                shipments[barcode].push(status);
            });

            for (const [barcode, statuses] of Object.entries(shipments)) {
                const lastStatus = statuses[0];
                const statusClass = getStatusClass(lastStatus);
                const statusText = getStatusText(lastStatus);

                html += `
                    <div class="shipment-card">
                        <div class="shipment-header">
                            <span class="barcode">${barcode}</span>
                            <span class="status-badge ${statusClass}">${statusText}</span>
                        </div>
                        <div class="timeline">
                `;

                statuses.forEach(status => {
                    html += `
                        <div class="timeline-item">
                            <div class="timeline-date">${formatDate(status.date)}</div>
                            <div class="timeline-status">${status.eventName || 'Status'}</div>
                            ${status.country ? `<div class="timeline-location">${status.country}</div>` : ''}
                        </div>
                    `;
                });

                html += '</div></div>';
            }

            resultsDiv.innerHTML = html;
        }

        function getStatusClass(status) {
            const name = (status.eventName || '').toLowerCase();
            if (name.includes('deliver')) return 'status-delivered';
            if (name.includes('depart') || name.includes('arriv') || name.includes('transit')) return 'status-transit';
            return 'status-pending';
        }

        function getStatusText(status) {
            const name = (status.eventName || '').toLowerCase();
            if (name.includes('deliver')) return 'Delivered';
            if (name.includes('depart') || name.includes('transit')) return 'In Transit';
            return 'Processing';
        }

        function formatDate(dateStr) {
            if (!dateStr) return '';
            try {
                return new Date(dateStr).toLocaleString('en-GB', {
                    day: '2-digit', month: '2-digit', year: 'numeric',
                    hour: '2-digit', minute: '2-digit'
                });
            } catch { return dateStr; }
        }
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    return render_template('index.html',
        countries=COUNTRIES,
        shipment_types=SHIPMENT_TYPES,
        categories=SHIPMENT_CATEGORIES,
        sender=SENDER,
        hs_codes=HS_CODES
    )


@app.route('/api/track', methods=['POST'])
def api_track():
    """Track shipments"""
    data = request.get_json()
    barcodes = data.get('barcodes', [])

    if not barcodes:
        return jsonify({"success": False, "error": "No barcodes provided"})

    if len(barcodes) == 1:
        result = track_shipment(barcodes[0])
    else:
        result = track_multiple(barcodes)

    return jsonify(result)


@app.route('/api/calculate')
def api_calculate():
    """Calculate shipping cost"""
    country = request.args.get('country')
    weight = request.args.get('weight', type=int)
    shipment_type = request.args.get('type', 'INTERNATIONAL')

    if not country or not weight:
        return jsonify({"success": False, "error": "Missing country or weight"})

    # Map API type to calc type
    type_mapping = {t["code"]: t.get("calcType", "SMALL_PACKAGE") for t in SHIPMENT_TYPES}
    calc_type = type_mapping.get(shipment_type, "SMALL_PACKAGE")

    result = calculate_shipping(country, weight, calc_type)
    return jsonify(result)


@app.route('/api/shipment', methods=['POST'])
def api_create_shipment():
    """Create international shipment"""
    data = request.get_json()

    # Get or create sender
    sender_result = get_or_create_sender()
    if not sender_result["success"]:
        return jsonify(sender_result)
    sender = sender_result["data"]

    # Create recipient address (international format)
    # Country must be ISO 3166-1 Alpha-2 code (e.g., "US", "PL", "DE")
    country_code = data["address"]["country"]
    # If full country name was passed, try to find the code
    if len(country_code) > 2:
        for c in COUNTRIES:
            if c["name"].lower() == country_code.lower():
                country_code = c["code"]
                break

    addr_data = {
        "country": country_code,
        "city": data["address"]["city"],
        "foreignStreetHouseApartment": data["address"]["address"],  # For international addresses
    }
    if data["address"].get("zipCode"):
        addr_data["postcode"] = data["address"]["zipCode"]
    if data["address"].get("region"):
        addr_data["region"] = data["address"]["region"]

    addr_result = create_address(addr_data)
    if not addr_result["success"]:
        return jsonify(addr_result)
    recipient_address_id = addr_result["data"]["id"]

    # Parse recipient name
    full_name = data["recipient"]["fullName"]
    name_parts = full_name.split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else name_parts[0]

    # Create recipient client
    recipient_data = {
        "name": full_name,
        "firstName": first_name,
        "lastName": last_name,
        "latinName": full_name,
        "phoneNumber": data["recipient"]["phone"].replace("+", "").replace(" ", "").replace("-", ""),
        "type": "INDIVIDUAL",
        "addressId": recipient_address_id
    }
    if data["recipient"].get("email"):
        recipient_data["email"] = data["recipient"]["email"]

    client_result = create_client(recipient_data)
    if not client_result["success"]:
        return jsonify(client_result)
    recipient_uuid = client_result["data"]["uuid"]

    # Create shipment
    shipment_type = data.get("type", "SMALL_BAG")

    # Get packageType from shipment types
    package_type = shipment_type  # Default
    for st in SHIPMENT_TYPES:
        if st["code"] == shipment_type:
            package_type = st.get("packageType", shipment_type)
            break

    # Check if this package type requires tracked and AVIA
    requires_tracked = False
    requires_avia = False
    for st in SHIPMENT_TYPES:
        if st["code"] == shipment_type:
            requires_tracked = st.get("requiresTracked", False)
            requires_avia = st.get("requiresAvia", False)
            break

    # Prepare parcel items for international shipment
    parcel_items = []
    for item in data.get("items", []):
        item_price = item.get("price", 10)
        parcel_items.append({
            "name": item.get("latinName", "Goods"),
            "latinName": item.get("latinName", "Goods"),
            "weight": item.get("weight", 100),
            "quantity": item.get("quantity", 1),
            "price": item_price,
            "value": item_price,  # Required for PRIME
            "currency": item.get("currency", "USD"),
            "hsCode": item.get("hsCode", "610910"),  # Default to T-shirts HS code
            "countryOfOrigin": item.get("countryOfOrigin", "UA")
        })

    # If no items provided, create default one
    if not parcel_items:
        default_price = data.get("declaredValue", 10)
        parcel_items.append({
            "name": "Goods",
            "latinName": "Goods",
            "weight": data["package"]["weight"],
            "quantity": 1,
            "price": default_price,
            "value": default_price,  # Required for PRIME
            "currency": data.get("currency", "USD"),
            "hsCode": "6109100000",  # Default to T-shirts HS code
            "countryOfOrigin": "UA"
        })

    # Build internationalData based on package type requirements
    international_data = {
        "categoryType": data.get("category", "GIFT"),
        "additionalInfo": data.get("euInfo", "")
    }

    # Add tracked and transportType for PRIME and other packages that require it
    if requires_tracked:
        international_data["tracked"] = True
    if requires_avia:
        international_data["transportType"] = "AVIA"

    # Calculate declared value in UAH (sum of all items' value converted to UAH)
    # Exchange rates (approximate)
    exchange_rates = {"UAH": 1, "USD": 41, "EUR": 44, "GBP": 51}
    total_declared_value = 0
    for item in parcel_items:
        item_value = item.get("value", 0) * item.get("quantity", 1)
        currency = item.get("currency", "USD")
        rate = exchange_rates.get(currency, 41)  # Default to USD rate
        total_declared_value += item_value * rate

    # Build parcel object
    parcel_data = {
        "weight": data["package"]["weight"],
        "length": data["package"].get("length", 10),
        "width": data["package"].get("width", 10),
        "height": data["package"].get("height", 10),
        "parcelItems": parcel_items  # Use parcelItems, not items!
    }

    # Add declaredPrice only for package types that support it
    # Only PARCEL and DECLARED_VALUE can have declared price according to Ukrposhta API
    if package_type in ["PARCEL", "DECLARED_VALUE"]:
        parcel_data["declaredPrice"] = total_declared_value

    shipment_data = {
        "sender": {"uuid": sender["uuid"]},
        "recipient": {"uuid": recipient_uuid},
        "senderAddressId": sender["addressId"],  # Number, not object!
        "recipientAddressId": recipient_address_id,  # Number, not object!
        "deliveryType": "W2W",
        "weight": data["package"]["weight"],
        "length": data["package"].get("length", 10),
        "width": data["package"].get("width", 10),
        "height": data["package"].get("height", 10),
        "packageType": package_type,
        "international": True,  # Required for international shipments
        "internationalData": international_data,
        "parcels": [parcel_data]
    }

    result = create_shipment(shipment_data)

    # Save to local file if successful
    if result.get("success") and result.get("data"):
        s = result["data"]
        save_shipment_locally({
            "uuid": s.get("uuid"),
            "barcode": s.get("barcode"),
            "type": data.get("type"),
            "status": s.get("status", "CREATED"),
            "deliveryPrice": s.get("deliveryPrice"),
            "weight": data["package"]["weight"],
            "created": datetime.now().isoformat(),
            "recipient": {
                "name": data["recipient"]["fullName"],
                "phoneNumber": data["recipient"]["phone"],
                "email": data["recipient"].get("email")
            },
            "recipientAddress": {
                "country": data["address"]["country"],
                "city": data["address"]["city"],
                "street": data["address"]["address"],
                "postcode": data["address"].get("zipCode")
            }
        })

    return jsonify(result)


@app.route('/api/label/<shipment_uuid>')
def api_get_label(shipment_uuid):
    """Get shipment label PDF

    Query params:
    - type: 'forms' (default), 'cn22', 'cn23', 'dl'
    """
    label_type = request.args.get('type', 'forms')
    pdf_data = get_shipment_label(shipment_uuid, label_type)
    if pdf_data:
        return Response(pdf_data, mimetype='application/pdf',
                       headers={'Content-Disposition': f'attachment; filename=label_{shipment_uuid}_{label_type}.pdf'})
    return jsonify({"success": False, "error": "Could not generate label. Make sure shipment UUID is correct."})


@app.route('/api/shipment-types')
def api_shipment_types():
    """Get available shipment types"""
    return jsonify({"success": True, "data": SHIPMENT_TYPES})


@app.route('/api/hs-codes')
def api_hs_codes():
    """Search HS codes"""
    query = request.args.get('q', '').lower()
    if not query or len(query) < 2:
        return jsonify({"success": True, "data": HS_CODES[:20]})

    results = [
        hs for hs in HS_CODES
        if query in hs['code'] or query in hs['description'].lower()
    ][:20]

    return jsonify({"success": True, "data": results})


@app.route('/api/countries')
def api_countries():
    """Get available countries"""
    return jsonify({"success": True, "data": COUNTRIES})


@app.route('/api/categories')
def api_categories():
    """Get available shipment categories"""
    return jsonify({"success": True, "data": SHIPMENT_CATEGORIES})


@app.route('/api/shipments')
def api_get_shipments():
    """Get list of shipments from Ukrposhta account"""
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    result = get_shipments_list(limit, offset)
    return jsonify(result)


@app.route('/api/shipment/<shipment_uuid>')
def api_get_shipment(shipment_uuid):
    """Get shipment details by UUID"""
    result = get_shipment_by_uuid(shipment_uuid)
    return jsonify(result)


@app.route('/api/shipment/<shipment_uuid>', methods=['DELETE'])
def api_delete_shipment(shipment_uuid):
    """Delete shipment (only works for CREATED status)"""
    result = delete_shipment(shipment_uuid)

    # Also remove from local storage if deletion was successful
    if result.get("success"):
        shipments = load_local_data(SHIPMENTS_FILE)
        shipments = [s for s in shipments if s.get("uuid") != shipment_uuid]
        save_local_data(SHIPMENTS_FILE, shipments)

    return jsonify(result)


@app.route('/api/debug/directories')
def api_debug_directories():
    """Get API directories/dictionaries"""
    env_cfg = get_env_config()
    headers = {
        "Authorization": f"Bearer {env_cfg['bearer_ecom']}",
        "Accept": "application/json"
    }
    params = {"token": env_cfg["counterparty_token"]}

    results = {}

    # Try to get various directories
    endpoints = [
        "/international/package-types",
        "/international/delivery-types",
        "/international/category-types",
        "/directories/package-types",
        "/directories/shipment-types",
        "/directories/delivery-types",
        "/classifiers/package-types",
    ]

    for endpoint in endpoints:
        try:
            url = f"{env_cfg['base_url']}/ecom/0.0.1{endpoint}"
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            results[endpoint] = {
                "status": resp.status_code,
                "body": resp.text[:500] if resp.text else None
            }
        except Exception as e:
            results[endpoint] = {"error": str(e)}

    return jsonify(results)


@app.route('/api/debug/test-shipment')
def api_debug_test_shipment():
    """Test shipment creation with minimal data"""
    env_cfg = get_env_config()

    # Get sender
    sender_result = get_or_create_sender()
    if not sender_result["success"]:
        return jsonify({"error": "Failed to create sender", "details": sender_result})

    sender = sender_result["data"]

    return jsonify({
        "sender_uuid": sender.get("uuid"),
        "sender_address_id": sender.get("addressId"),
        "counterparty_uuid": env_cfg["counterparty_uuid"],
        "message": "Sender created successfully. Check console for debug output when creating shipment."
    })


@app.route('/api/debug/shipment-schema')
def api_debug_shipment_schema():
    """Try to get shipment schema or example"""
    env_cfg = get_env_config()
    headers = {
        "Authorization": f"Bearer {env_cfg['bearer_ecom']}",
        "Accept": "application/json"
    }

    results = {}

    # Try swagger/openapi endpoints
    endpoints = [
        "/ecom/0.0.1/swagger",
        "/ecom/0.0.1/api-docs",
        "/ecom/0.0.1/openapi",
        "/ecom/0.0.1/international-doc",
    ]

    for endpoint in endpoints:
        try:
            url = f"{env_cfg['base_url']}{endpoint}"
            resp = requests.get(url, headers=headers, timeout=10)
            results[endpoint] = {
                "status": resp.status_code,
                "content_type": resp.headers.get("Content-Type", ""),
                "body_preview": resp.text[:300] if resp.text else None
            }
        except Exception as e:
            results[endpoint] = {"error": str(e)}

    return jsonify(results)


@app.route('/api/debug/update-sender-latinname')
def api_debug_update_sender_latinname():
    """Update sender's latinName (required for USA shipments)"""
    env_cfg = get_env_config()
    latin_name = request.args.get('latinName', SENDER.get('latinName', 'Lozovyi Ihor Hryhorovych'))
    sender_uuid = env_cfg["counterparty_uuid"]

    # Try to update sender directly without fetching first (avoids 403 on GET)
    update_data = {
        "latinName": latin_name
    }

    update_result = update_client(sender_uuid, update_data)
    if update_result["success"]:
        return jsonify({
            "success": True,
            "message": "Sender latinName updated successfully",
            "latinName": latin_name,
            "sender_uuid": sender_uuid
        })
    else:
        return jsonify({
            "success": False,
            "error": "Could not update sender",
            "details": update_result,
            "note": "You may need to update latinName via Ukrposhta personal cabinet (ok.ukrposhta.ua)"
        })


@app.route('/api/debug/validate-hs-code')
def api_debug_validate_hs_code():
    """Test HS code validation via Ukrposhta API"""
    env_cfg = get_env_config()
    headers = {
        "Authorization": f"Bearer {env_cfg['bearer_ecom']}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    code = request.args.get('code', '6109100010')

    # Try various API endpoints that might validate HS codes
    results = {
        "tested_code": code,
        "endpoints_tried": []
    }

    endpoints = [
        f"/ecom/0.0.1/international-doc/hs-codes?code={code}",
        f"/ecom/0.0.1/international-doc/hs-codes/{code}",
        f"/ecom/0.0.1/hs-codes?code={code}",
        f"/ecom/0.0.1/hs-codes/{code}",
        f"/ecom/0.0.1/directories/hs-codes?code={code}",
        f"/ecom/0.0.1/directory/hs-codes?code={code}",
    ]

    for endpoint in endpoints:
        try:
            url = f"{env_cfg['base_url']}{endpoint}"
            resp = requests.get(url, headers=headers, timeout=10)
            results["endpoints_tried"].append({
                "endpoint": endpoint,
                "status": resp.status_code,
                "response": resp.text[:500] if resp.text else None
            })
        except Exception as e:
            results["endpoints_tried"].append({
                "endpoint": endpoint,
                "error": str(e)
            })

    return jsonify(results)


@app.route('/api/debug/test-prime-shipment')
def api_debug_test_prime_shipment():
    """Test PRIME shipment creation with a valid structure based on official documentation"""
    env_cfg = get_env_config()

    # Get sender first
    sender_result = get_or_create_sender()
    if not sender_result["success"]:
        return jsonify({"success": False, "error": "Could not get sender", "details": sender_result})

    sender = sender_result["data"]

    # Official PRIME shipment structure from documentation (International_documentation_26012026.html)
    # Key points:
    # - senderAddressId as number (not object)
    # - international: true
    # - parcelItems with: latinName, description, quantity, value, weight, countryOfOrigin, hsCode
    # - internationalData with: transportType=AVIA, tracked=true, categoryType, daysForReturn
    # - hsCode: 6-10 digits only
    test_structure = {
        "sender": {"uuid": sender["uuid"]},
        "recipient": {"uuid": "RECIPIENT_UUID_HERE"},
        "senderAddressId": sender["addressId"],  # Number, not object!
        "recipientAddressId": "RECIPIENT_ADDRESS_ID",  # Number
        "packageType": "PRIME",
        "deliveryType": "W2W",
        "weight": 200,
        "length": 30,
        "width": 0,  # Can be 0 for PRIME
        "height": 0,  # Can be 0 for PRIME
        "international": True,
        "internationalData": {
            "transportType": "AVIA",
            "categoryType": "GIFT",  # or MIXED_CONTENT (requires explanation field)
            "tracked": True,
            "daysForReturn": 30,
            "aviaReturn": False
        },
        "parcels": [{
            "weight": 200,
            "length": 30,
            "width": 0,
            "height": 0,
            "parcelItems": [{
                "latinName": "Cotton T-shirt",  # Required, max 32 chars, no forbidden words
                "description": "Blue cotton t-shirt",  # Optional description
                "quantity": 1,
                "value": 50,  # Cost for customs (required)
                "weight": 200,
                "countryOfOrigin": "UA",  # ISO 3166-1 Alpha-2
                "hsCode": "6109100000"  # 6-10 digits, must be valid UKTZED code
            }]
        }]
    }

    # Forbidden words in latinName: BRYUKI, ACCESSORIES, GIFT, GIFT BOX, GIFTS,
    # HANDMADE GIFT, PRESENT, SOUVENIR, Other, item, cadeau, or only digits

    return jsonify({
        "success": True,
        "sender": sender,
        "prime_shipment_structure": test_structure,
        "notes": {
            "hsCode": "Must be 6-10 digits, valid UKTZED code",
            "latinName": "Max 32 chars, forbidden: GIFT, ACCESSORIES, PRESENT, SOUVENIR, item, cadeau, only digits",
            "value": "Max 3,000,000 UAH or 50,000 USD/EUR/GBP",
            "tracked": "Must be True for PRIME",
            "transportType": "Must be AVIA for PRIME",
            "PRIME_countries": "Estonia, Lithuania, Morocco, Oman, UAE, Egypt, France, Netherlands, Norway, Poland, Portugal, Romania, USA, UK, Germany, etc."
        }
    })


@app.route('/api/import-shipment', methods=['POST'])
def api_import_shipment():
    """Import existing shipment by barcode (from personal account)"""
    data = request.get_json()
    barcode = data.get("barcode", "").strip()

    if not barcode:
        return jsonify({"success": False, "error": "Barcode is required"})

    # Check if already imported
    shipments = load_local_data(SHIPMENTS_FILE)
    if any(s.get("barcode") == barcode for s in shipments):
        return jsonify({"success": False, "error": "Shipment already imported"})

    # Get tracking info
    tracking = track_shipment(barcode)
    if not tracking.get("success"):
        return jsonify({"success": False, "error": "Could not find shipment with this barcode"})

    statuses = tracking.get("data", [])
    status = statuses[0].get("eventName") if statuses else "UNKNOWN"

    # Save locally
    save_shipment_locally({
        "barcode": barcode,
        "uuid": None,
        "type": "IMPORTED",
        "status": status,
        "created": datetime.now().isoformat(),
        "imported": True,
        "recipient": data.get("recipient", {}),
        "recipientAddress": data.get("address", {})
    })

    return jsonify({"success": True, "data": {"barcode": barcode, "status": status}})


if __name__ == '__main__':
    print("=" * 50)
    print("Ukrposhta - International Shipments")
    print("=" * 50)
    print("\nStarting web server...")
    print("Open in browser: http://localhost:5000")
    print("\nPress Ctrl+C to stop")
    print("=" * 50)

    app.run(debug=True, host='0.0.0.0', port=5000)
