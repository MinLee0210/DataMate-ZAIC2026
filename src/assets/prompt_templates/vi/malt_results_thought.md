Hãy suy luận trên kết quả của các truy vấn dữ liệu trước khi đưa ra đáp án cuối cùng. Đáp án sai bị
trừ một điểm còn không trả lời thì không mất gì: chỉ đưa đáp án cuối cùng khi bạn tin nó đúng.

## Lược đồ (DuckDB)
```yaml
{{schema}}
```

## Thời gian đã được xác định
{{time}}

## Câu hỏi
{{question}}

## Suy luận của bạn đến giờ
{{thought}}

## Truy vấn dữ liệu và kết quả
{{data}}

## Hình dạng đáp án mà câu hỏi yêu cầu (rulebook §9)
{{shape}}
Hình dạng này không làm câu không trả lời được thành trả lời được: nếu dữ liệu thật sự không có
đáp án, hãy nói không trả lời được (kèm bằng chứng) thay vì ép một giá trị vào hình dạng.

Kiểm tra lần lượt các điểm sau, và hãy từ chối trả lời (abstain) khi một điểm không đạt mà bạn không
sửa được:
- Đơn vị và quy mô: đúng đơn vị câu hỏi hỏi (hộp hay viên, VND), phần trăm tính theo điểm phần
  trăm (66,01 chứ không phải 0,66), đếm hay tính tiền.
- Cách viết: trạng thái và khách lẻ phải khớp bằng `is_cancelled`, `is_returned`, `is_walk_in`, không
  chỉ một cách viết. Số đếm hoặc tỉ lệ bằng 0 thường là do bỏ sót một cách viết.
- Cảnh báo: dòng `Warning: The value ... does not occur in any column` nghĩa là bộ lọc dùng giá trị
  không có trong dữ liệu, nên kết quả sai hoặc rỗng. Hãy dùng một giá trị thật được liệt kê (hoặc
  `LIKE`) rồi chạy lại truy vấn.
- Hình dạng: câu hỏi dạng danh sách trả một cột theo đúng thứ tự được hỏi; "so sánh A với B" trả số
  theo thứ tự A, B; chỉ trả bảng khi câu hỏi cần nhiều cột.
- Tính hợp lý: so sánh bậc độ lớn với các giá trị mẫu (lỗi gấp ×10, ×100, ×1000).

Đồng thời đối chiếu kết quả với câu hỏi và rulebook: khoảng thời gian và quy tắc as_of_date, bản ghi
hợp lệ, định nghĩa và đơn vị của đại lượng, đối tượng, chiều xếp hạng, đồng hạng thì xếp theo mã
tăng dần và top-k, làm tròn và kiểu đáp án, và tính hợp lý (kết quả rỗng hoặc NULL, dấu hay độ lớn
bất thường, 0 so với "không có dữ liệu"). Lỗi của một truy vấn có thể khắc phục: hãy sửa hoặc thử
cách khác.

Tên các kết quả bạn có thể dùng: {{names}}

Chỉ coi câu hỏi là không thể trả lời (unanswerable) khi dữ liệu thật sự không có: khoảng thời gian
nằm hoàn toàn ngoài dữ liệu, hoặc cửa hàng không ghi nhận loại thông tin đó. Câu hỏi KHÔNG phải là
unanswerable khi đại lượng có thể tính từ các cột khác (số lượng × đơn giá − giảm giá dòng), khi một
giá trị được viết khác đi, khi cột ngày cần được phân tích cú pháp, hoặc khi một kỳ nằm trong phạm vi
dữ liệu nhưng không có dòng nào (khi đó đáp án là 0, hoặc bộ lọc sai). Hãy sửa truy vấn.

Sau đó chọn một hành động và chỉ trả lời bằng một đối tượng JSON, không viết gì thêm:
{{actions}}
