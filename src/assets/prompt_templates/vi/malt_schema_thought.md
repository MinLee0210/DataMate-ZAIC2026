Bạn trả lời một câu hỏi về dữ liệu của cửa hàng này theo từng bước, như một trợ lý phân tích dữ liệu:
suy luận trên lược đồ, kiểm tra giá trị thật, truy vấn, rồi suy luận trên kết quả.
Đây là bước đầu tiên: suy luận trên lược đồ. Chưa viết SQL.

## Cửa hàng
{{readme}}

## Lược đồ (DuckDB)
```yaml
{{schema}}
```

## Các view ngữ nghĩa có sẵn
{{semantic}}

## Thời gian đã được xác định
{{time}}

## Thực thể khớp trong câu hỏi (văn bản câu hỏi -> bảng.cột = giá trị)
{{entities}}

## Cách tiếp cận
{{approach}}

## Câu hỏi
{{question}}

Trong `thought`, lần lượt trình bày:
1. Nhu cầu: chủ cửa hàng muốn biết gì, trong một câu; giải nghĩa từ khẩu ngữ, từ thiếu dấu và từ
   viết tắt ("sp" = sản phẩm, "dc" = được, "nhiu" = nhiêu, "dthu" = doanh thu).
2. Ánh xạ thuật ngữ: tách câu hỏi thành các thuật ngữ nghiệp vụ (đại lượng, đối tượng, thời gian,
   điều kiện, xếp hạng) và ánh xạ từng thuật ngữ: `thuật ngữ -> bảng.cột / quy tắc trong rulebook /
   giá trị`. Khi hai cột hoặc hai quy tắc đều có thể khớp, nêu cả hai, chọn một và giải thích vì sao.
   Trích quy tắc rulebook áp dụng (phần chung và phần của loại hình cửa hàng này).
3. Phạm vi thời gian: khoảng ngày, cột ngày áp dụng cho từng khoảng, và quy tắc ngày hiện tại
   (as_of_date): các bản ghi sau ngày này có trong dữ liệu nhưng không được tính.
4. Đáp án: kiểu đáp án và định dạng, hoặc lý do dữ liệu có thể không trả lời được.

Sau đó liệt kê trong `sample_fields` tối đa 8 `bảng.cột` mà bạn cần xem giá trị hoặc khoảng giá trị
thật trước khi viết truy vấn: các cột lọc (trạng thái, nhóm hàng, đơn vị tính, tên) và các cột ngày.

Chỉ trả lời bằng một đối tượng JSON, không viết gì thêm:
{"thought": "...", "sample_fields": ["bảng.cột", ...]}
