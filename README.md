# Notary ERP

## Giới thiệu
Dự án này là một ứng dụng FastAPI phục vụ nghiệp vụ công chứng (notary), tập trung vào quản lý hồ sơ (case) và sinh văn bản hợp đồng từ mẫu DOCX.

## Cấu trúc thư mục

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
│   └── routers/              # (Hiện trống) dự kiến tách router theo module
├── templates/                # Template tài liệu
│   └── contract_transfer.docx # Mẫu hợp đồng chuyển nhượng
├── scripts/                  # Script hỗ trợ thủ công
│   ├── make_template_content.py # Tạo nội dung template
│   └── test_generate_contract.py# Script test sinh hợp đồng
├── requirements.txt          # Danh sách phụ thuộc Python
├── app__init__.py            # File bổ trợ (hiện không dùng)
└── README.md                 # Tài liệu dự án
```

## Luồng chức năng chính
- **Tạo hồ sơ (case)**: API tạo case, lưu thông tin tài sản và các bên tham gia.
- **Sinh hợp đồng**: Dựa vào template DOCX trong `templates/`, hệ thống thay thế placeholder và lưu file trong `data/files/`.
- **Tải tài liệu**: API trả về file DOCX đã sinh.

## Gợi ý khởi chạy nhanh
1. Cài dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Chạy ứng dụng (ví dụ dùng uvicorn):
   ```bash
   uvicorn app.main:app --reload
   ```
3. Truy cập tài liệu API: `http://localhost:8000/docs`
