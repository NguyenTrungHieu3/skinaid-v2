# 📋 BÁO CÁO PHÂN TÍCH: Chuyển Đổi Hệ Thống eSIM từ Aloo → Hải Trần

> **Ngày lập:** 13/04/2026  
> **Mục đích:** Liệt kê toàn bộ các vị trí trong source code cần thay đổi khi chuyển từ nhà cung cấp Aloo sang Hải Trần  
> **Phạm vi:** Backend only — giao diện (UI) giữ nguyên tạm thời  
> **Phương án clone:** Copy ra repo/folder riêng biệt hoàn toàn  

---

## MỤC LỤC

1. [Tóm tắt tổng quan](#1-tóm-tắt-tổng-quan)
2. [Nhóm 1 — Cấu hình môi trường (.env)](#2-nhóm-1--cấu-hình-môi-trường-env)
3. [Nhóm 2 — Lớp API Integration (PHP)](#3-nhóm-2--lớp-api-integration-php)
4. [Nhóm 3 — Frontend gọi API Vendor (Vue.js / JS)](#4-nhóm-3--frontend-gọi-api-vendor-vuejs--js)
5. [Nhóm 4 — Webhook nhận callback từ Vendor](#5-nhóm-4--webhook-nhận-callback-từ-vendor)
6. [Nhóm 5 — Database / Migration](#6-nhóm-5--database--migration)
7. [Nhóm 6 — Artisan Commands (CLI)](#7-nhóm-6--artisan-commands-cli)
8. [Nhóm 7 — Email Templates](#8-nhóm-7--email-templates)
9. [Nhóm 8 — File ngôn ngữ (Lang)](#9-nhóm-8--file-ngôn-ngữ-lang)
10. [Nhóm 9 — Blade Views (Frontend tĩnh)](#10-nhóm-9--blade-views-frontend-tĩnh)
11. [Nhóm 10 — Route definitions](#11-nhóm-10--route-definitions)
12. [Ước lượng mức độ ảnh hưởng](#12-ước-lượng-mức-độ-ảnh-hưởng)
13. [Thông tin cần thu thập từ Hải Trần](#13-thông-tin-cần-thu-thập-từ-hải-trần)
14. [Rủi ro & Kịch bản xử lý](#14-rủi-ro--kịch-bản-xử-lý)

---

## 1. Tóm Tắt Tổng Quan

### Hệ thống hiện tại hoạt động thế nào?

```
Khách hàng (Browser)
      │
      ▼
Website Laravel này ──── gọi API ──→ Aloo (aloo.com.vn) = Vendor Mẹ
  "Cửa hàng bán lẻ"                    "Tổng kho eSIM"
  ❌ Không tự phát hành eSIM            ✅ Phát hành QR, Activation Code
  ❌ Không xử lý VNPay trực tiếp       ✅ Tạo link VNPay, xác minh giao dịch
```

### Mục tiêu chuyển đổi

| Hạng mục | Hiện tại (Aloo) | Sau chuyển đổi (Hải Trần) |
|----------|-----------------|---------------------------|
| API Base URL | `https://staging.aloo.com.vn/` | `<URL mới từ Hải Trần>` |
| API Key | `1165ab97...aa7322` | `<Key mới từ Hải Trần>` |
| Class name | `ApiAlo` | `ApiHaiTran` |
| Biến .env | `ALO_KEY_API`, `ALO_BASE_URL` | `HAITAN_KEY_API`, `HAITAN_BASE_URL` |
| agency_code | `'aloo'` | `<mã đại lý Hải Trần>` |
| Email gửi từ | `CSKH ALOO` | `CSKH Hải Trần` |
| Tên app | `ESIM_ALOO` | `ESIM_HAITAN` |

### Tổng quan số lượng file ảnh hưởng

| Nhóm | Số file | Mức ưu tiên | Độ phức tạp |
|------|---------|-------------|-------------|
| Cấu hình .env | 3 file | 🔴 Cao | Thấp |
| API Integration (PHP) | 1 file + 5 file gọi | 🔴 Cao | Trung bình ↔ Cao |
| Frontend API (Vue/JS) | 4 file | 🔴 Cao | Trung bình |
| Webhook | 2 route, 1 controller | 🔴 Cao | Trung bình |
| Database | 1 migration + sửa 1 cột | 🟡 Trung bình | Thấp |
| Artisan Commands | 3 file | 🟡 Trung bình | Thấp |
| Email Templates | 2 file | 🟡 Trung bình | Thấp |
| File ngôn ngữ | 38 file (19 vi + 19 en) | 🟠 Thấp* | Thấp (tìm/thay) |
| Blade Views | ~8 file | 🟠 Thấp* | Thấp |
| Routes | 2 file | 🟡 Trung bình | Thấp |

> \* Các mục "Thấp" vì sếp nói giao diện giữ nguyên tạm thời, nhưng nếu làm luôn thì cũng đơn giản (find & replace).

---

## 2. Nhóm 1 — Cấu Hình Môi Trường (.env)

> [!IMPORTANT]
> Đây là bước **đầu tiên và đơn giản nhất**. Chỉ cần thay value, không sửa code.

### File cần sửa: `.env`, `.env.example`, `.env.local`

| Dòng | Biến cũ | Giá trị cũ | Đổi thành |
|------|---------|------------|-----------|
| 2 | `APP_NAME` | `ESIM_ALOO` | `ESIM_HAITAN` |
| 7 | `ALO_KEY_API` | `1165ab97669b46f413c8cf0ad8e1fdee58aa7322` | → Đổi tên biến thành `HAITAN_KEY_API` + giá trị mới |
| 8 | `ALO_BASE_URL` | `https://staging.aloo.com.vn/` | → Đổi tên biến thành `HAITAN_BASE_URL` + giá trị mới |
| 15 | `APP_URL` | `http://127.0.0.1:8000` | Domain production mới |
| 22 | `MAIL_USERNAME` | `quynh.hoang@rikai.technology` | Email SMTP Hải Trần |
| 23 | `MAIL_PASSWORD` | `orhptcrsjxuiyjbf` | App password mới |
| 25 | `MAIL_FROM_ADDRESS` | `quynh.hoang@rikai.technology` | Email from Hải Trần |
| 26 | `MAIL_FROM_NAME` | `"CSKH ALOO"` | `"CSKH HẢI TRẦN"` |
| 30 | `GOOGLE_CLIENT_ID` | `285514454501-...` | Client ID mới (dự án Google Cloud mới) |
| 31 | `GOOGLE_CLIENT_SECRET` | `GOCSPX-...` | Secret mới |
| 32 | `GOOGLE_REDIRECT_URI` | `http://127.0.0.1:8000/callback` | `https://<domain_haitan>/callback` |
| 85 | `VITE_API_TOKEN` | `1165ab97...aa7322` | Token/Key mới |

> [!WARNING]
> File `.env` hiện tại có **2 block `APP_NAME` / `APP_KEY` trùng lặp** (dòng 2-5 và dòng 11-14). Cần dọn dẹp khi chuyển đổi.

### ⚡ Hành động cần thiết:
- Đổi **tên biến** `ALO_KEY_API` → `HAITAN_KEY_API` (kéo theo phải sửa code PHP — xem Nhóm 2)
- Đổi **tên biến** `ALO_BASE_URL` → `HAITAN_BASE_URL`
- Tạo project Google Cloud Console mới cho Hải Trần
- Tạo app Facebook Developers mới cho Hải Trần
- Tạo tài khoản email SMTP mới

---

## 3. Nhóm 2 — Lớp API Integration (PHP)

> [!CAUTION]
> Đây là phần **quan trọng nhất** và **rủi ro cao nhất**. Nếu API Hải Trần khác cấu trúc Aloo, phải viết lại logic.

### 3.1. File trung tâm: [Helper/ApiAlo.php](file:///e:/aloo_esim_ec_web_laravel/Helper/ApiAlo.php) (26 dòng)

```php
// HIỆN TẠI — File 26 dòng, class duy nhất kết nối vendor
class ApiAlo {
    public function __construct() {
        $this->headerApi = [
            'Authorization' => env('ALO_KEY_API'),     // ← Đổi tên biến
        ];
        $this->base_url = env('ALO_BASE_URL');         // ← Đổi tên biến
    }
    public function postAlo(string $url, $param) { ... }  // ← Đổi tên method
    public function getAlo(string $url, $param) { ... }    // ← Đổi tên method
}
```

**Cần đổi:**
| Hạng mục | Cũ | Mới |
|----------|-----|------|
| Tên class | `ApiAlo` | `ApiHaiTran` |
| Tên file | `ApiAlo.php` | `ApiHaiTran.php` |
| Namespace | `Helper\ApiAlo` | `Helper\ApiHaiTran` |
| Biến env | `env('ALO_KEY_API')` | `env('HAITAN_KEY_API')` |
| Biến env | `env('ALO_BASE_URL')` | `env('HAITAN_BASE_URL')` |
| Tên method | `postAlo()` | `postHaiTran()` (hoặc `post()`) |
| Tên method | `getAlo()` | `getHaiTran()` (hoặc `get()`) |

### 3.2. Tất cả file PHP đang inject/dùng `ApiAlo` (6 file)

Sau khi đổi tên class, **tất cả 6 file sau phải cập nhật `use` statement và tham chiếu:**

| # | File | Dòng | Nội dung cần sửa |
|---|------|------|-------------------|
| 1 | [HomeController.php](file:///e:/aloo_esim_ec_web_laravel/Modules/Ecommerce/App/Http/Controllers/HomeController.php) | 7, 21 | `use Helper\ApiAlo;` → `use Helper\ApiHaiTran;` + `ApiAlo $api_alo` → `ApiHaiTran $api_ht` |
| 2 | [CartController.php](file:///e:/aloo_esim_ec_web_laravel/Modules/Ecommerce/App/Http/Controllers/CartController.php) | 10, 309, 383 | Tương tự + 10 chỗ gọi `$api_alo->postAlo(...)` → `$api_ht->postHaiTran(...)` |
| 3 | [ApiController.php](file:///e:/aloo_esim_ec_web_laravel/app/Http/Controllers/ApiController.php) | 7, 17, 28, 31, 36 | `use Helper\ApiAlo;` + `env('ALO_KEY_API')` trong webhook + method `updateAlo()` |
| 4 | [ApiCommand.php](file:///e:/aloo_esim_ec_web_laravel/app/Console/Commands/ApiCommand.php) | 6, 32, 49 | `use Helper\ApiAlo;` + `$api_alo->postAlo(...)` |
| 5 | [CacheGlobalPlans.php](file:///e:/aloo_esim_ec_web_laravel/app/Console/Commands/CacheGlobalPlans.php) | 6, 14, 21 | `use Helper\ApiAlo;` + `$apiAlo->postAlo(...)` |
| 6 | [CacheValidCountries.php](file:///e:/aloo_esim_ec_web_laravel/app/Console/Commands/CacheValidCountries.php) | 7, 14, 22 | `use Helper\ApiAlo;` + `$api_alo->postAlo(...)` |

### 3.3. Các API Endpoint paths cần kiểm tra/sửa

Hệ thống hiện gọi **7 endpoint** của Aloo. Nếu Hải Trần dùng URL paths khác, phải sửa từng chỗ:

| # | Endpoint Path (Aloo) | Gọi từ file PHP | Gọi từ file Vue/JS | Tổng chỗ gọi |
|---|----------------------|-----------------|---------------------|---------------|
| 1 | `/collaborator/api/v2/getGlobalPlans` | `ApiCommand.php` (L43,48), `CacheGlobalPlans.php` (L20,21), `CacheValidCountries.php` (L20,21), `HomeController.php` (L26,33) | `Index.vue` (Admin, L15) | **9 chỗ** |
| 2 | `/collaborator/api/v2/verifyVNPAY` | `CartController.php` (L319, L390, L405) | — | **3 chỗ** |
| 3 | `/collaborator/api/v2/verifyVnpay` | `CartController.php` (L334) | — | **1 chỗ** |
| 4 | `/collaborator/api/v2/getOrders` | `CartController.php` (L327, L398, L412) | — | **3 chỗ** |
| 5 | `/collaborator/api/v2/getEsims` | `CartController.php` (L420) | — | **1 chỗ** |
| 6 | `/collaborator/api/v2/orderEsims` | — | `Payment.vue` (L470), `Payone.vue` (L392) | **2 chỗ** |
| 7 | `/collaborator/api/v2/checkCoupon` | — | `Discount.vue` (L56) | **1 chỗ** |

**Tổng: 20 chỗ cần kiểm tra/sửa endpoint paths**

### 3.4. Cấu trúc Request/Response cần kiểm tra tương thích

> [!CAUTION]
> Nếu API Hải Trần trả JSON khác cấu trúc, phải sửa **TOÀN BỘ logic parse response**

**Request format hiện tại (gửi cho Aloo):**
```json
{ "param": { "url": "/collaborator/api/v2/...", "agency_code": "" } }
```

**Response format hiện tại (nhận từ Aloo):**

| Endpoint | Cấu trúc response | Các key được đọc trong code |
|----------|-------------------|----------------------------|
| `getGlobalPlans` | `result.data.{country_list, single_country_plan, region_country_plan, region_list}` | 4 keys |
| `verifyVnpay` | `result.transaction_id`, `result.error` | 2 keys |
| `getOrders` | `result.data` | 1 key |
| `getEsims` | `result.data.{esim_qr_link, card_data, activation_code, download_url, issue_date, expire_date}` | 6 keys |

**File chịu ảnh hưởng nặng nhất nếu response khác:**
- [CartController.php](file:///e:/aloo_esim_ec_web_laravel/Modules/Ecommerce/App/Http/Controllers/CartController.php) — Lines 309–448 (140 dòng logic parse response)
- [ApiCommand.php](file:///e:/aloo_esim_ec_web_laravel/app/Console/Commands/ApiCommand.php) — Lines 41–130 (logic import gói eSIM, parse `aloo_product_code`, `agency_code`)

---

## 4. Nhóm 3 — Frontend Gọi API Vendor (Vue.js / JS)

> [!WARNING]
> Tuy sếp nói giữ nguyên giao diện, nhưng 4 file dưới đây **gọi trực tiếp API vendor** nên BẮT BUỘC phải sửa ở backend lẫn frontend.

### 4.1. [api.js](file:///e:/aloo_esim_ec_web_laravel/Modules/Ecommerce/resources/assets/js/api.js) — **Hardcoded Base URL + API Key!**

```js
// HIỆN TẠI — Line 4 & 7
const api = axios.create({
    baseURL: 'https://staging.aloo.com.vn/'     // ← HARDCODED, phải đổi
})
const token = '1165ab97669b46f413c8cf0ad8e1fdee58aa7322'  // ← HARDCODED, phải đổi
```

**Cần đổi:**
- `baseURL` → Base URL mới của Hải Trần
- `token` → API Key mới (hoặc tốt hơn, đọc từ `VITE_API_TOKEN` trong `.env`)

### 4.2. [Payment.vue](file:///e:/aloo_esim_ec_web_laravel/Modules/Ecommerce/resources/assets/js/Payment.vue)

| Dòng | Nội dung | Hành động |
|------|----------|-----------|
| 320 | `product_code: item.package.aloo_product_code` | Đổi key nếu rename cột DB |
| 470 | `url: '/collaborator/api/v2/orderEsims'` | Đổi endpoint path nếu Hải Trần khác |
| 475 | `agency_code: 'aloo'` | **Đổi thành mã đại lý Hải Trần** |

### 4.3. [Payone.vue](file:///e:/aloo_esim_ec_web_laravel/Modules/Ecommerce/resources/assets/js/Payone.vue)

| Dòng | Nội dung | Hành động |
|------|----------|-----------|
| 392 | `url: '/collaborator/api/v2/orderEsims'` | Đổi endpoint path |
| 398 | `product_code: cart.value.aloo_product_code` | Đổi key nếu rename cột DB |
| 404 | `agency_code: 'aloo'` | **Đổi thành mã đại lý Hải Trần** |

### 4.4. [Discount.vue](file:///e:/aloo_esim_ec_web_laravel/Modules/Ecommerce/resources/assets/js/components/Discount.vue)

| Dòng | Nội dung | Hành động |
|------|----------|-----------|
| 56 | `url: '/collaborator/api/v2/checkCoupon'` | Đổi endpoint path nếu Hải Trần khác |

### 4.5. [Search.vue](file:///e:/aloo_esim_ec_web_laravel/Modules/Ecommerce/resources/assets/js/components/Search.vue)

| Dòng | Nội dung | Hành động |
|------|----------|-----------|
| 110 | `const CACHE_KEY = "aloo_esim_cache_v1";` | Đổi thành `"haitan_esim_cache_v1"` |

### 4.6. [Index.vue](file:///e:/aloo_esim_ec_web_laravel/Modules/Admin/resources/views/Vue/pages/Index.vue) (Admin Panel)

| Dòng | Nội dung | Hành động |
|------|----------|-----------|
| 15 | `url:'/collaborator/api/v2/getGlobalPlans'` | Đổi endpoint path |
| 16 | `agency_code:"aloo"` | **Đổi thành mã đại lý Hải Trần** |

> [!IMPORTANT]
> Sau khi sửa Vue/JS files, **PHẢI chạy lại `npm run build`** để generate bundle mới.

---

## 5. Nhóm 4 — Webhook Nhận Callback Từ Vendor

### File: [ApiController.php](file:///e:/aloo_esim_ec_web_laravel/app/Http/Controllers/ApiController.php)

| Method | Route | Mục đích | Cần đổi |
|--------|-------|----------|---------|
| `success()` L34 | `POST /api/success-payment` | Nhận eSIM data từ vendor (QR, card_data, activation_code) | Sửa xác thực: `env('ALO_KEY_API')` → `env('HAITAN_KEY_API')` |
| `updateAlo()` L17 | `GET /api/admin-update` | Vendor gọi để trigger đồng bộ gói eSIM | Đổi tên method: `updateAlo()` → `updateHaiTran()` |
| `payment()` L28 | `POST /alo/payment` | Proxy gọi API vendor tạo payment | Sửa class inject `ApiAlo` → `ApiHaiTran` |

> [!WARNING]
> **Webhook `POST /api/success-payment`** là cơ chế Aloo **gọi ngược vào** hệ thống để thông báo eSIM sẵn sàng. Cần hỏi Hải Trần:
> 1. Có cơ chế webhook tương tự không?
> 2. Format request giống hay khác?
> 3. Xác thực bằng cách nào? (API key trong body? Header?)

---

## 6. Nhóm 5 — Database / Migration

### 6.1. Cột `aloo_product_code` trong bảng `packages`

**File migration:** [2025_02_18_083936_package.php](file:///e:/aloo_esim_ec_web_laravel/database/migrations/2025_02_18_083936_package.php) L16
```php
$table->string('aloo_product_code')->unique();
```

**Nếu đổi tên cột** (chờ sếp xác nhận):
- Cần tạo migration mới: `rename_aloo_product_code_to_product_code`
- Sửa tất cả code PHP dùng `aloo_product_code` (4 chỗ trong `ApiCommand.php`)
- Sửa `Payment.vue` L320 và `Payone.vue` L398

### 6.2. Cột `agency_code` trong bảng `packages`

- Dữ liệu hiện tại có giá trị `'aloo'` — sẽ tự thay đổi khi import từ API mới
- Không cần migration, chỉ cần chạy lại `php artisan api:admin` sau khi đổi API

### 6.3. Database mới

- Nếu deploy server riêng → tạo DB mới hoàn toàn, chạy `php artisan migrate`
- Nếu dùng chung server → tạo database name khác (VD: `esim_haitan`)

---

## 7. Nhóm 6 — Artisan Commands (CLI)

| # | File | Command | Cần đổi |
|---|------|---------|---------|
| 1 | [AdminCommand.php](file:///e:/aloo_esim_ec_web_laravel/app/Console/Commands/AdminCommand.php) | `rikai:make:admin-alo` | Đổi signature → `rikai:make:admin-haitan`, đổi description, default email `admin@alo.com` → mới |
| 2 | [ApiCommand.php](file:///e:/aloo_esim_ec_web_laravel/app/Console/Commands/ApiCommand.php) | `api:admin` | Sửa inject `ApiAlo` + dùng `postAlo()` + parse `aloo_product_code` (4 chỗ: L71, L76, L107, L109) |
| 3 | [CacheGlobalPlans.php](file:///e:/aloo_esim_ec_web_laravel/app/Console/Commands/CacheGlobalPlans.php) | `cache:global-plans` | Sửa inject `ApiAlo` + endpoint URL |
| 4 | [CacheValidCountries.php](file:///e:/aloo_esim_ec_web_laravel/app/Console/Commands/CacheValidCountries.php) | `cache:valid-countries` | Sửa inject `ApiAlo` + endpoint URL |

### Kernel.php — Scheduled Command

[Kernel.php](file:///e:/aloo_esim_ec_web_laravel/app/Console/Kernel.php) L16:
```php
$schedule->command('api:admin')->daily();  // Đồng bộ gói eSIM từ vendor — Chạy hàng ngày
```
→ Không cần sửa (tên command `api:admin` giữ nguyên).

---

## 8. Nhóm 7 — Email Templates

### 8.1. [sendmail.blade.php](file:///e:/aloo_esim_ec_web_laravel/Modules/Ecommerce/resources/views/orders/sendmail.blade.php)

Email gửi QR code eSIM cho khách hàng sau thanh toán. **10+ vị trí chứa "Aloo":**

| Dòng | Nội dung | Loại |
|------|----------|------|
| 10 | `<img src="https://staging.aloo.com.vn/vi/country/media/3/image"` | Logo Aloo — cần thay |
| 16 | `sử dụng dịch vụ eSIM của ALOO!` | Text branding |
| 94, 96 | `src="https://staging.aloo.com.vn/vi/country/media/2/image"` | Icon từ CDN Aloo |
| 103 | `ALOO sẽ không thể hỗ trợ...` | Text branding |
| 141, 143, 198, 200 | `src="https://staging.aloo.com.vn/..."` | Icons từ CDN Aloo |
| 222 | `Fanpage ALOO hoặc qua Zalo: 0379097744` | Thông tin liên hệ |
| 225 | `Đội ngũ chăm sóc khách hàng ALOO.` | Text branding |
| 227 | `src="https://staging.aloo.com.vn/country/media/10/image"` | Logo footer email |

> **Hành động:** Download icons/images từ CDN Aloo, thay bằng assets của Hải Trần hoặc host local.

### 8.2. [reset_password_mail.blade.php](file:///e:/aloo_esim_ec_web_laravel/Modules/Ecommerce/resources/views/reset_password/reset_password_mail.blade.php)

| Dòng | Nội dung | Hành động |
|------|----------|-----------|
| 12 | `contact.aloo@aloo.jp` | Đổi email |
| 13 | `facebook.com/aloo.jp` | Đổi link Facebook |
| 15 | `Đội ngũ Aloo.` | Đổi tên |

---

## 9. Nhóm 8 — File Ngôn Ngữ (Lang)

> [!NOTE]
> Sếp nói giao diện giữ nguyên tạm thời. Tuy nhiên, nếu muốn làm luôn thì chỉ cần **find & replace** toàn bộ.
>
> Nếu chưa đổi giao diện, **có thể bỏ qua nhóm này** và để lại cho phase sau.

### Danh sách 38 file lang chứa "Aloo"

#### Tiếng Việt (`resources/lang/vi/`) — 19 file, **14 file có "Aloo"**

| File | Nội dung cần đổi |
|------|-------------------|
| `terms.php` | "CÔNG TY TNHH ALOO" (11 chỗ), hotline `037-909-7744`, "ALOO.JP" |
| `privacy_policy.php` | "CÔNG TY TNHH ALOO" (6 chỗ), "ALOO.JP" |
| `home.php` | "Aloo cung cấp..." (4 chỗ), review khách hàng nhắc Aloo |
| `about.php` | "Aloo Japan" (7 chỗ), toàn bộ giới thiệu công ty |
| `install.php` | "Aloo cung cấp" (3 chỗ), "ALOO.JP" |
| `contact.php` | "ALOO" (5 chỗ), email `contact.aloo@aloo.jp`, hotline |
| `footer.php` | "CÔNG TY TRÁCH NHIỆM HỮU HẠN ALOO", "Aloo Japan" |
| `check_device.php` | "Aloo eSIM" (2 chỗ), "ALOO 24/7" |
| `questions.php` | "ALOO.JP" (1 chỗ) |
| `profile.php` | "ALOO.JP" (1 chỗ) |
| `profile_order.php` | "ALOO.JP" (1 chỗ) |
| `profile_myesim.php` | "ALOO.JP" (1 chỗ) |
| `profile_setting.php` | "ALOO.JP" (1 chỗ) |
| `payment.php` / `multi_payment.php` / `blog.php` | "ALOO.JP" (mỗi file 1 chỗ) |

#### Tiếng Anh (`resources/lang/en/`) — 19 file, **~14 file tương tự**

Cùng nội dung nhưng bằng tiếng Anh: "ALOO CO., LTD.", "ALOO.JP", "Aloo offers eSIM..." v.v.

### Cách thực hiện nhanh (khi được approve làm)

```
Tìm & thay trong thư mục resources/lang/:
  "CÔNG TY TNHH ALOO"     → "<Tên công ty Hải Trần>"
  "ALOO CO., LTD."         → "<Tên tiếng Anh Hải Trần>"
  "ALOO.JP"                → "<Tên app Hải Trần>"
  "Aloo Japan"             → "<Tên thương hiệu Hải Trần>"
  "Aloo"                   → "<Hải Trần>"  (cẩn thận duyệt từng cái)
  "aloo"                   → "<hải trần>"
  "037-909-7744"           → "<hotline mới>"
  "contact.aloo@aloo.jp"   → "<email mới>"
```

---

## 10. Nhóm 9 — Blade Views (Frontend Tĩnh)

> Tương tự Nhóm 8, tạm thời có thể để lại vì sếp nói giữ nguyên UI.

### Danh sách file chứa "Aloo"

| File | Nội dung "Aloo" |
|------|-----------------|
| [layout_home.blade.php](file:///e:/aloo_esim_ec_web_laravel/Modules/Ecommerce/resources/views/layouts/layout_home.blade.php) | Title `Esim Aloo` (L22), nội dung `eSIM Aloo` (L109), link App Store/Play Store (L149-150) |
| [footer.blade.php](file:///e:/aloo_esim_ec_web_laravel/Modules/Ecommerce/resources/views/components/footer.blade.php) | Email, Facebook, YouTube, TikTok Aloo, icons từ CDN Aloo |
| [subfooter.blade.php](file:///e:/aloo_esim_ec_web_laravel/Modules/Ecommerce/resources/views/components/subfooter.blade.php) | Link App Store/Play Store Aloo |
| [headercomponent.blade.php](file:///e:/aloo_esim_ec_web_laravel/Modules/Ecommerce/resources/views/components/headercomponent.blade.php) | Link blog `aloo.com.vn/blog-vi/` |
| [term.blade.php](file:///e:/aloo_esim_ec_web_laravel/Modules/Ecommerce/resources/views/pages/term.blade.php) | 3 link `esim.aloo.com.vn` |
| [privacy_policy.blade.php](file:///e:/aloo_esim_ec_web_laravel/Modules/Ecommerce/resources/views/pages/privacy_policy.blade.php) | 2 link `esim.aloo.com.vn` |
| [landing_page.blade.php](file:///e:/aloo_esim_ec_web_laravel/Modules/Ecommerce/resources/views/pages/landing_page.blade.php) | 2 link `esim.aloo.com.vn` |
| [listesim.blade.php](file:///e:/aloo_esim_ec_web_laravel/Modules/Ecommerce/resources/views/pages/listesim.blade.php) | Link App Store Aloo |
| [installs.blade.php](file:///e:/aloo_esim_ec_web_laravel/Modules/Ecommerce/resources/views/installs/installs.blade.php) | Link App Store/Play Store |
| [Phone.vue](file:///e:/aloo_esim_ec_web_laravel/Modules/Ecommerce/resources/assets/js/components/Phone.vue) | "activation code provided by Aloo" (L235) |

---

## 11. Nhóm 10 — Route Definitions

| File | Dòng | Route | Cần đổi |
|------|------|-------|---------|
| [routes/api.php](file:///e:/aloo_esim_ec_web_laravel/routes/api.php) | 29 | `Route::get('/admin-update', [ApiController::class, 'updateAlo'])` | Method name `updateAlo` → `updateHaiTran` |
| Modules/Ecommerce/routes/web.php | ~150 | `POST /alo/payment` | Đổi route path nếu muốn clean |
| Modules/Ecommerce/routes/api.php | — | `POST /api/success-payment` | Giữ nguyên path, chỉ sửa logic xác thực bên trong |

---

## 12. Ước Lượng Mức Độ Ảnh Hưởng

### Kịch bản A: API Hải Trần **TƯƠNG THÍCH** (cùng cấu trúc request/response)

| Phân loại | Số file sửa | Thời gian ước tính |
|-----------|-------------|-------------------|
| 🟢 Đổi tên + giá trị đơn giản (find/replace) | ~35 file | **2-3 ngày** |
| 🟡 Sửa logic code (class rename, endpoint paths) | ~12 file | **2-3 ngày** |
| 🔵 Test end-to-end | — | **2-3 ngày** |
| **Tổng** | **~47 file** | **~1-2 tuần** |

### Kịch bản B: API Hải Trần **KHÔNG TƯƠNG THÍCH** (khác cấu trúc)

| Phân loại | Số file sửa | Thời gian ước tính |
|-----------|-------------|-------------------|
| 🟢 Tất cả của kịch bản A | ~47 file | **1 tuần** |
| 🔴 Viết lại logic parse response | 4-6 file | **1-2 tuần** thêm |
| 🔴 Viết adapter/mapping layer | 1-2 file mới | **2-3 ngày** |
| 🔵 Test end-to-end + fix bugs | — | **1 tuần** |
| **Tổng** | **~50+ file** | **~3-4 tuần** |

---

## 13. Thông Tin Cần Thu Thập Từ Hải Trần

> [!IMPORTANT]
> Trước khi bắt tay code, **BẮT BUỘC** phải có những thông tin sau từ Hải Trần:

### Kỹ thuật (ưu tiên cao nhất)

| # | Thông tin | Tại sao cần | Ảnh hưởng nếu thiếu |
|---|-----------|-------------|---------------------|
| 1 | **Base URL API** (production + staging) | Để cấu hình `.env` | ❌ Không thể bắt đầu |
| 2 | **API Key** + cách xác thực (Header nào? Format?) | Để cấu hình `ApiHaiTran.php` | ❌ Không thể kết nối |
| 3 | **Tài liệu API** (endpoint list, request/response format) | Để biết có cần viết lại logic không | ❌ Rủi ro rất cao |
| 4 | **Cơ chế Webhook** (Hải Trần gọi ngược vào hệ thống?) | Để cấu hình nhận eSIM | ❌ eSIM sẽ không được gửi cho khách |
| 5 | **VNPay** — dùng riêng hay qua API Hải Trần? | Ảnh hưởng flows thanh toán | ⚠️ Có thể phải sửa nhiều |
| 6 | **Mã đại lý** (`agency_code`) cho website này | Hardcoded trong Vue.js | ❌ Đơn hàng sẽ không được ghi nhận |

### Thương hiệu (ưu tiên trung bình — cho phase 2)

| # | Thông tin | Dùng ở đâu |
|---|-----------|-----------|
| 7 | Tên thương hiệu chính thức (VN + EN) | Lang files, email, footer |
| 8 | Logo (header, footer, favicon, email) | Views, email template |
| 9 | Email liên hệ, hotline, Zalo | Footer, email, lang files |
| 10 | Facebook, YouTube, TikTok (nếu có) | Footer |
| 11 | Có mobile app riêng không? (iOS/Android link) | Footer, subfooter, installs page |
| 12 | Link blog riêng hay dùng blog trong hệ thống? | Header menu |

### Hạ tầng (ưu tiên trung bình)

| # | Thông tin | Dùng ở đâu |
|---|-----------|-----------|
| 13 | Domain website mới | `.env`, OAuth redirect, nginx, SSL |
| 14 | Server riêng hay dùng chung? | Docker, MySQL, deploy |
| 15 | Tài khoản Google Cloud / Facebook App | OAuth login |
| 16 | Tài khoản SMTP email | Gửi email cho khách |

---

## 14. Rủi Ro & Kịch Bản Xử Lý

| # | Rủi ro | Mức độ | Kịch bản xử lý |
|---|--------|--------|----------------|
| 1 | API Hải Trần khác hoàn toàn cấu trúc | 🔴 Cao | Viết **Adapter Layer** — class trung gian chuyển đổi request/response |
| 2 | API Hải Trần không có webhook | 🔴 Cao | Hệ thống phải tự polling API để kiểm tra eSIM sẵn sàng → sửa flow đáng kể |
| 3 | Hải Trần dùng cổng thanh toán khác (không VNPay) | 🟡 TB | Phải viết integration cổng thanh toán mới |
| 4 | `api.js` hardcode API key + URL | 🟡 TB | Chuyển sang đọc từ env/config Vite |
| 5 | `agency_code` hardcode 3 chỗ trong Vue.js | 🟡 TB | Sửa + rebuild JS bundle |
| 6 | Email images load từ CDN Aloo (staging.aloo.com.vn) | 🟡 TB | Download & host local hoặc trên CDN Hải Trần |
| 7 | File `.env` có 2 block trùng lặp | 🟢 Thấp | Dọn dẹp khi clone |

---

## Phụ Lục: Bảng Tổng Hợp Tất Cả File Cần Sửa

### Bắt buộc sửa (Backend/API)

| # | File | Loại thay đổi | Mô tả |
|---|------|---------------|-------|
| 1 | `.env` | Config | Đổi tên + giá trị biến |
| 2 | `.env.example` | Config | Đổi tên + giá trị biến |
| 3 | `.env.local` | Config | Đổi tên + giá trị biến |
| 4 | `Helper/ApiAlo.php` | Rename + sửa code | → `Helper/ApiHaiTran.php`, đổi env, đổi tên method |
| 5 | `app/Http/Controllers/ApiController.php` | Sửa code | Đổi import, biến, method name |
| 6 | `Modules/Ecommerce/.../CartController.php` | Sửa code | Đổi import, 10 chỗ gọi API, parse response |
| 7 | `Modules/Ecommerce/.../HomeController.php` | Sửa code | Đổi import, endpoint URL |
| 8 | `app/Console/Commands/ApiCommand.php` | Sửa code | Đổi import, endpoint, `aloo_product_code` |
| 9 | `app/Console/Commands/CacheGlobalPlans.php` | Sửa code | Đổi import, endpoint |
| 10 | `app/Console/Commands/CacheValidCountries.php` | Sửa code | Đổi import, endpoint |
| 11 | `app/Console/Commands/AdminCommand.php` | Sửa code | Đổi signature, description, default email |
| 12 | `Modules/Ecommerce/.../js/api.js` | Sửa code | Đổi hardcoded baseURL + token |
| 13 | `Modules/Ecommerce/.../js/Payment.vue` | Sửa code | Đổi endpoint, agency_code, product_code key |
| 14 | `Modules/Ecommerce/.../js/Payone.vue` | Sửa code | Đổi endpoint, agency_code, product_code key |
| 15 | `Modules/Ecommerce/.../js/components/Discount.vue` | Sửa code | Đổi endpoint |
| 16 | `Modules/Ecommerce/.../js/components/Search.vue` | Sửa code | Đổi cache key |
| 17 | `Modules/Admin/.../Vue/pages/Index.vue` | Sửa code | Đổi endpoint, agency_code |
| 18 | `routes/api.php` | Sửa route | Đổi method name reference |

### Cần sửa nhưng có thể để phase sau (Branding/UI)

| # | File | Loại | Số vị trí "Aloo" |
|---|------|------|-------------------|
| 19-20 | Email templates (2 file) | Blade | ~15 chỗ |
| 21-58 | Lang files (38 file vi+en) | PHP | ~100+ chỗ |
| 59-66 | Blade views (8 file) | Blade | ~20 chỗ |

**Tổng cộng: ~18 file bắt buộc (backend) + ~48 file branding (tùy chọn phase sau) = ~66 file**
