---
name: ranking-rules
description: Cách xếp hạng (bán chạy nhất, top-N, cao nhất, thấp nhất) và xử lý đồng hạng. Dùng cho mọi câu hỏi xếp hạng hoặc chọn giá trị lớn nhất, nhỏ nhất.
---

# Quy tắc xếp hạng

- Xếp hạng theo tiêu chí mà câu hỏi nêu ("doanh thu", "số lượng", "số đơn"). Nếu không nêu tiêu chí
  nào, dùng tiêu chí mặc định của rulebook (xem kỹ năng business-metrics).
- Chỉ xếp hạng trên các đơn hợp lệ (xem kỹ năng business-metrics).
- Sắp xếp giảm dần cho "nhiều nhất / cao nhất / bán chạy nhất / top", tăng dần cho
  "ít nhất / thấp nhất / bán chậm nhất".
- Đồng hạng thì xếp theo mã mục tăng dần: `ORDER BY metric DESC, code ASC`.
- Top-N: `LIMIT N` sau toàn bộ ORDER BY. "Nhất" đứng một mình nghĩa là N = 1 và kiểu đáp án là string.
- Trả về tên của mục, trừ khi câu hỏi hỏi mã.
