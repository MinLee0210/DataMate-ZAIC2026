---
name: answer-types
description: Chọn kiểu đáp án và định hình kết quả SQL để chấm điểm chính xác. Dùng cho mọi câu hỏi.
---

# Kiểu đáp án

Chọn đúng một kiểu; kết quả truy vấn phải có hình dạng như bảng dưới.

| Kiểu | Hình dạng kết quả | Ghi chú |
|---|---|---|
| number | 1 dòng, 1 cột | số đếm, tổng, trung bình. Hệ thống tự làm tròn 2 chữ số thập phân. |
| percent | 1 dòng, 1 cột | tính theo điểm phần trăm: 12.5 nghĩa là 12,5%. Tỉ lệ phải nhân 100. Giữ dấu (tăng trưởng có thể âm). |
| string | 1 dòng, 1 cột | một tên hoặc một mã. Trả về tên, trừ khi câu hỏi hỏi mã. |
| date | 1 dòng, 1 cột | một DATE, hoặc `strftime(d, '%Y-%m')` khi câu hỏi hỏi về tháng. |
| boolean | 1 dòng, 1 cột | `true` / `false` (câu hỏi có/không). |
| list | 1 cột, N dòng | có thứ tự: top-N, "những sản phẩm nào". Sắp xếp theo quy tắc xếp hạng. |
| table | N cột, N dòng | nhiều giá trị cho mỗi mục, ví dụ sản phẩm và doanh thu. Sắp xếp theo quy tắc xếp hạng. |
| unanswerable | không có SQL | dữ liệu không có cột, khái niệm hay kỳ thời gian mà câu hỏi cần. |

- "bao nhiêu" → number. "bao nhiêu phần trăm", "tỉ lệ", "tăng/giảm bao nhiêu %" → percent.
- "khi nào", "ngày nào", "tháng nào" → date. "có ... không" → boolean.
- "top 3", "những ... nào" → list. Hỏi một mục kèm giá trị của nó → table.
- Một mục tốt nhất/kém nhất ("sản phẩm nào bán chạy nhất") → string.
- Trả đúng hình dạng mà câu hỏi hỏi, không phải kết quả phong phú nhất: "những sản phẩm nào" mà
  không hỏi giá trị → list (chỉ tên); "có … không", "đúng không" → boolean dù đã tính một con số để
  quyết định; table chỉ khi câu hỏi hỏi một mục **và** giá trị của nó.
