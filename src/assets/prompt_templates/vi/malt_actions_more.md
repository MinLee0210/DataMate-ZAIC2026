- Đáp án cuối cùng lấy từ một kết quả, kết quả đó phải đã là đáp án (một dòng một cột cho number,
  percent, string, date và boolean; một cột cho list; cả bảng cho table):
  `{"thought": "...", "action": "final", "answer_type": "number|percent|string|date|boolean|list|table", "data_result": "<tên kết quả>", "confidence": 0.0}`.
  `data_result` là **tên** của kết quả như đã liệt kê ở trên (ví dụ `total_revenue`), không phải giá
  trị và không phải một con số.
  `confidence` là xác suất trung thực của bạn (từ 0 đến 1) rằng đúng giá trị này là đáp án đúng:
  khoảng 0,9 chỉ khi truy vấn tuân thủ mọi quy tắc áp dụng và đã qua mọi bước kiểm tra ở trên;
  khoảng 0,5 khi một quy tắc, một đơn vị hoặc một cách viết còn chưa chắc; thấp hơn khi kết quả có vẻ lạ.
  Đáp án sai bị trừ một điểm còn không trả lời thì không mất gì, nên độ tin cậy thấp sẽ không được trả lời.
- Dữ liệu không trả lời được câu hỏi (khoảng thời gian nằm hoàn toàn ngoài dữ liệu, hoặc cửa hàng
  không ghi nhận điều này): `{"thought": "...", "action": "final", "answer_type": "unanswerable", "reason": "...", "evidence": "...", "confidence": 0.0}`.
  `reason` viết bằng tiếng Việt. `evidence` nêu cái còn thiếu: khái niệm mà không bảng hay cột nào ghi
  nhận (sau khi đã kiểm tra lược đồ và giá trị mẫu), hoặc khoảng thời gian cùng ngày đầu và ngày cuối
  của dữ liệu. Không có bằng chứng đó thì không phải unanswerable: hãy sửa truy vấn hoặc abstain.
- Phân tích các kết quả đã lấy bằng pandas. Đoạn mã thấy được `results` (dict các DataFrame ở trên,
  theo tên), `pd` và `query(sql)` (trả về DataFrame); không được import; phải gán đáp án vào
  `result`. Bạn sẽ thấy đầu ra của nó trước khi đưa đáp án cuối cùng:
  `{"thought": "...", "action": "analysis", "question": "...", "data_result_names": ["..."], "code": "result = ..."}`
- Chạy thêm một truy vấn dữ liệu (ví dụ để sửa lỗi hoặc sửa bộ lọc sai). Bạn sẽ thấy kết quả của nó
  trước khi đưa đáp án cuối cùng:
  `{"thought": "...", "action": "data_query", "name": "ten_snake_case", "question": "...", "sql": "SELECT ..."}`
- Không đủ tự tin vào đáp án nào: `{"thought": "...", "action": "abstain", "reason": "..."}`
