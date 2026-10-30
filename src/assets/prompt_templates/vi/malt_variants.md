Dùng cách làm trực tiếp nhất cho câu hỏi này.
---
Làm từ dưới lên: bắt đầu từ bảng chi tiết (dòng hàng), áp dụng mọi bộ lọc trên các dòng rồi mới tổng hợp. Dựng trước tập đơn hợp lệ rồi nối (join) với nó.
---
Kiểm chứng độc lập: lấy các dòng cần thiết bằng một truy vấn thuần, rồi tính đáp án trong một bước phân tích pandas thay vì một phép tổng hợp SQL; kiểm tra đơn vị và cách viết trên các dòng gốc.
---
Bắt đầu từ rulebook: viết ra định nghĩa chính xác trong rulebook của từng thuật ngữ nghiệp vụ trong câu hỏi (bản ghi hợp lệ, doanh thu, kỳ thời gian, xếp hạng, làm tròn) trước khi truy vấn, rồi dựng truy vấn khớp từng định nghĩa đó.
---
Tính đáp án bằng hai cách độc lập, ví dụ qua bảng đơn và qua bảng dòng hàng, hoặc có và không có phép nối; dùng cách khớp với rulebook, và nếu hai cách khác nhau thì tìm hiểu vì sao trước khi trả lời.
---
Phòng thủ với dữ liệu: đếm số dòng trước và sau mỗi bộ lọc, xem các giá trị khác nhau của mọi cột được lọc, và xử lý rõ ràng cách viết, NULL và số dạng văn bản; rồi mới tổng hợp.
