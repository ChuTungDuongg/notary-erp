# Notary ERP ✨

## Giới thiệu 🌷
Dự án này là một ứng dụng FastAPI phục vụ nghiệp vụ công chứng (notary), tập trung vào quản lý hồ sơ (case) và sinh văn bản hợp đồng từ mẫu DOCX.

## Mục tiêu 🎯
- Quản lý hồ sơ công chứng rõ ràng, dễ truy vết.
- Tự động hoá sinh hợp đồng từ template DOCX.
- Hỗ trợ luồng làm việc nhanh, ít thao tác thủ công.

## Tính năng chính 💡
- 🗂️ **Quản lý hồ sơ (case)**: lưu thông tin tài sản và các bên tham gia.
- 📝 **Sinh hợp đồng**: thay thế placeholder trong template DOCX và xuất file.
- 📥 **Tải tài liệu**: trả về file DOCX đã sinh qua API.
- 🔎 **Tìm kiếm hồ sơ**: lọc nhanh theo mã hồ sơ, CCCD, tên, địa chỉ tài sản.

## Cấu trúc thư mục 📁

```
.
├── app/                      # Mã nguồn chính của ứng dụng FastAPI
│   ├── main.py               # Điểm vào ứng dụng, khai báo API routes
│   ├── db.py                 # Khởi tạo và quản lý kết nối cơ sở dữ liệu
│   ├── models/               # ORM models (SQLAlchemy)
│   │   ├── base.py           # Base model/metadata
│   │   ├── case.py           # Model hồ sơ (case)
│   │   ├── case_party.py     # Bảng liên kết case - party (vai trò mua/bán)
│   │   ├── document.py       # Model tài liệu, loại tài liệu và version
│   │   ├── party.py          # Model người tham gia (buyer/seller)
│   │   └── property.py       # Model tài sản/bất động sản
│   ├── schemas/              # Pydantic schemas cho request/response
│   │   ├── case.py           # Schema cho case (tạo mới, chi tiết, danh sách)
│   │   └── document.py       # Schema cho document
│   ├── services/             # Logic nghiệp vụ
│   │   ├── case_service.py   # Tạo hồ sơ, xử lý dữ liệu liên quan
│   │   └── document_generator.py # Sinh hợp đồng từ template DOCX
│   └── routers/              # Các API routers
├── templates/                # Template tài liệu
│   └── contract_transfer.docx # Mẫu hợp đồng chuyển nhượng
├── scripts/                  # Script hỗ trợ thủ công
│   ├── make_template_content.py # Tạo nội dung template
│   └── test_generate_contract.py# Script test sinh hợp đồng
├── requirements.txt          # Danh sách phụ thuộc Python
├── app__init__.py            # File bổ trợ (hiện không dùng)
└── README.md                 # Tài liệu dự án
```

## Luồng chức năng chính 🔄
1. **Tạo hồ sơ (case)**: API tạo case, lưu thông tin tài sản và các bên tham gia.
2. **Sinh hợp đồng**: Dựa vào template DOCX trong `templates/`, hệ thống thay thế placeholder và lưu file trong `data/files/`.
3. **Tải tài liệu**: API trả về file DOCX đã sinh.

## Yêu cầu hệ thống ✅
- Python 3.10+ (khuyến nghị dùng môi trường ảo).
- SQLite (tự tạo file `notary_erp.db` ở thư mục gốc khi chạy lần đầu).

## Cài đặt & chạy nhanh 🚀
1. Tạo môi trường ảo và cài dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Chạy ứng dụng (ví dụ dùng uvicorn):
   ```bash
   uvicorn app.main:app --reload
   ```
3. Truy cập tài liệu API: `http://localhost:8000/docs`

## Ví dụ gọi API nhanh 🔍
- **Tạo hồ sơ**
  ```bash
  curl -X POST http://localhost:8000/cases \
    -H "Content-Type: application/json" \
    -d '{
  "code": "CA-001",
  "case_type": "TRANSFER_LAND",
  "signing_date": "2024-01-12",
  "transfer_price": 600000000,
  "parties": [
    {
      "full_name": "Nguyen Van A",
      "cccd": "012345678901",
      "role": "SELLER"
    },
    {
      "full_name": "Tran Thi B",
      "cccd": "098765432109",
      "role": "BUYER"
    }
  ],
  "property": {
    "address": "123 Nguyen Trai, Q1, HCM",
    "map_sheet_no": "12",
    "parcel_no": "34",
    "area_m2": 80.5,
    "certificate_no": "GCN-ABC-123"
  }
}'
  ```
- **Sinh hợp đồng**
  ```bash
  curl -X POST http://localhost:8000/cases/1/generate-contract
  ```
- **Tìm kiếm hồ sơ**
  ```bash
  curl "http://localhost:8000/cases/search?q=Nguyen%20Van%20A"
  ```

## Gợi ý vận hành 🧩
- Template DOCX nằm trong `templates/`. Khi thay đổi placeholder, cần đồng bộ với logic trong `document_generator.py`.
- File hợp đồng sinh ra được lưu tại `data/files/<case_code>/`.
- Có thể chạy script `scripts/test_generate_contract.py` để kiểm thử nhanh luồng sinh hợp đồng.

## Ghi chú nhỏ 💬
- Nên dùng môi trường ảo (venv/conda) để quản lý dependency gọn gàng.
- Nếu cần đổi template, hãy thay file trong `templates/` và đảm bảo placeholder khớp dữ liệu đầu vào.
