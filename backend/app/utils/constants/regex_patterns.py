# Regex pattern cho validation

# Email validation:
# - Bắt đầu bằng chữ cái, số, hoặc ký tự . _ + -
# - Sau ký tự @ là domain (chỉ gồm chữ, số, dấu -)
# - Domain phải có dấu chấm . và phần TLD (vd: .com, .org, .vn)
EMAIL_PATTERN = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

# Password validation:
# - Ít nhất 8 ký tự
# - Chứa ít nhất 1 chữ thường
# - Chứa ít nhất 1 chữ hoa
# - Chứa ít nhất 1 chữ số
# - Chứa ít nhất 1 ký tự đặc biệt (không phải chữ hoặc số)
PASSWORD_PATTERN = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z\d]).{8,}$'

# Phone number validation:
# - Có thể bắt đầu bằng dấu "+"
# - Sau đó chỉ chứa số
# - Độ dài từ 8 đến 15 ký tự
PHONE_PATTERN = r'^\+?[0-9]{8,15}$'
