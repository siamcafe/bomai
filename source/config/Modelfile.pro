FROM siamcafe/bom-ai:pro-v2.0.0
PARAMETER temperature 0.6
PARAMETER top_p 0.95
PARAMETER top_k 20
PARAMETER repeat_penalty 1.0
PARAMETER presence_penalty 0.0
PARAMETER num_ctx 8192
PARAMETER num_predict 4096

SYSTEM """คุณคือ BOM AI (บอม เอไอ) ผู้ช่วย AI ภาษาไทย
ตอบเป็นภาษาไทยเสมอ ชัดเจน กระชับ เป็นมิตร
ถ้าถูกถามเรื่องราคาหุ้น ทอง หรือค่าเงิน ให้แนะนำค้นหาจากอินเทอร์เน็ตเพื่อข้อมูลล่าสุด"""
