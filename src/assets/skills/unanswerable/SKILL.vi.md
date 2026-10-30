---
name: unanswerable
description: Khi nào trả lời "unanswerable" thay vì viết SQL. Dùng khi câu hỏi hỏi điều mà dữ liệu có thể không có.
---

# Câu hỏi không thể trả lời

Đáp án sai bị trừ một điểm; trả lời "unanswerable" đúng cho một câu thật sự không thể trả lời thì
được một điểm. Trả lời `unanswerable` (không SQL) khi:

- câu hỏi cần một khái niệm mà không bảng hay cột nào có (ví dụ lợi nhuận mà không có cột giá vốn,
  tuổi khách hàng mà không có ngày sinh, đánh giá sao mà không có bảng đánh giá);
- kỳ thời gian nằm hoàn toàn ngoài phạm vi ngày của dữ liệu (xem khoảng giá trị cột trong lược đồ),
  hoặc nằm ở tương lai so với `as_of_date`;
- câu hỏi nêu một thực thể (sản phẩm, khách hàng, chi nhánh) không khớp với gì trong dữ liệu;
- câu hỏi không liên quan đến dữ liệu của cửa hàng này.

Không trả lời `unanswerable` chỉ vì truy vấn khó. Câu hỏi có kết quả bằng 0 hoặc tập rỗng trong một
kỳ mà dữ liệu bao phủ là câu hỏi trả lời được (đáp án là 0, hoặc false).
