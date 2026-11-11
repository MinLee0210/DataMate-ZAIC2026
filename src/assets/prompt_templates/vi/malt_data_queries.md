Bước thứ hai: lập các truy vấn dữ liệu, sau khi đã suy luận trên lược đồ và xem các giá trị mẫu.

## Lược đồ (DuckDB)
```yaml
{{schema}}
```

## View ngữ nghĩa (đã áp rulebook §1 và §3)
{{semantic}}
Ưu tiên view `v_*` khi nó trả lời được câu hỏi: view đã loại đơn huỷ/trả, dùng ngày đặt và coi
khách là mã. Không suy lại các luật đó.

## Thời gian đã được xác định
{{time}}

## Thực thể khớp trong câu hỏi
{{entities}}

## Cách tiếp cận
{{approach}}

## Câu hỏi
{{question}}

## Suy luận của bạn đến giờ
{{thought}}

## Giá trị mẫu
{{samples}}

## Ví dụ đã giải ở các cửa hàng khác
Các truy vấn đã được kiểm chứng cho câu hỏi tương tự ở cửa hàng khác. Bảng và cột của chúng không
phải của cửa hàng này: hãy tái sử dụng cách làm (bộ lọc, quy tắc rulebook, nhóm, làm tròn), tuyệt đối
không dùng lại tên bảng hay cột.
{{examples}}

## Hình dạng đáp án (rulebook §9)
{{shape}}
Hình dạng này là đáp án khi dữ liệu trả lời được; nó không làm câu không trả lời được thành trả
lời được.

Viết từ 1 đến 3 truy vấn dữ liệu có tên. Mỗi truy vấn là một câu `SELECT` DuckDB chỉ-đọc (được dùng
CTE) trên các bảng ở trên. Khi có thể, hãy để một truy vấn trả về đúng đáp án: đã tính, đã làm tròn và
đã sắp xếp như đáp án yêu cầu. Chỉ dùng các truy vấn khác để kiểm tra điều mà đáp án phụ thuộc vào.
Áp dụng rulebook: bản ghi hợp lệ, đúng cột ngày và khoảng ngày, quy tắc as_of_date, đơn vị tính.

Chỉ trả lời bằng một đối tượng JSON, không viết gì thêm:
{"thought": "các truy vấn trả lời câu hỏi như thế nào",
 "data_queries": [{"name": "ten_snake_case", "question": "truy vấn này trả lời điều gì", "sql": "SELECT ..."}]}
