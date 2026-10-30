---
name: messy-data
description: Các tệp gốc của cửa hàng lộn xộn ra sao, ingest đã làm sạch gì, và cách kiểm tra, sửa phần còn lại bằng SQL hoặc pandas. Dùng khi một cột, bảng hoặc kết quả trông sai, trước khi tin nó.
---

# Dữ liệu lộn xộn

Ingest làm sạch các trường hợp phổ biến trước khi bạn thấy các bảng. Hãy biết nó đã làm gì, và tự
kiểm tra phần còn lại: lấy mẫu cột, rồi sửa trong truy vấn (SQL) hoặc trong một bước phân tích (pandas).

## Ingest đã làm sạch
- **Tiền và số** là cột số. `50.000đ` = 50000 (VND không có phần thập phân, dấu chấm ngăn hàng
  nghìn), `25k` = 25000, `1,5tr` / `2 triệu` = 1500000 / 2000000, `30 nghìn` = 30000.
- **Bảng bị tách đã được gộp.** Các sheet tách theo tháng (`T01_2025`, `T02_2025`, …) và các tệp tách
  thành phần (`DonHang_1`, `DonHang_2026`, `Lo_1`, `Lo_2`) có cùng cột là một bảng. Cột `nguon` ghi
  tệp và sheet của từng dòng. Truy vấn bảng đã gộp; đừng tự UNION.
- **Xuất theo nhóm đã được điền xuống.** Khi mã đơn, ngày, trạng thái và khách hàng chỉ ghi ở dòng
  đầu của đơn, các dòng sau đã được điền lại (rulebook §8).
- **Dòng trùng của một đơn đã bị bỏ.** Hai dòng của cùng một đơn giống nhau ở mọi ô chỉ tính một
  lần (rulebook §8). Các dòng giống nhau ở bảng không có mã đơn được giữ nguyên.
- **Ngày** trong một cột được viết nhiều kiểu (`29/11/2025`, `30 thg 5 2026`, số ngày Excel như
  `45678`) là một cột ngày; ngày không có năm lấy năm của sheet (rulebook §8).
- **Dòng tổng/phụ** (`Tổng ngày 30/05`, `Cộng ngày …`, `TỔNG THÁNG`, `Cộng`) và **dòng tiêu đề lặp lại**
  trong sheet đã bị xóa. Đừng tự cộng thêm tổng lên trên các dòng chi tiết.
- **Tiêu đề** được tìm bên dưới các dòng tựa đề; ô gộp lặp lại giá trị của nó.

## Kiểm tra trước khi tin một kết quả
- Cột tiền hoặc số lượng vẫn là `VARCHAR`: ingest không phân tích được một số giá trị. Lấy mẫu chúng,
  rồi chuyển đổi trong SQL, ví dụ `TRY_CAST(regexp_replace(lower(col), '[^0-9k]', '', 'g') ...)`,
  hoặc trong pandas.
- Giá trị nhỏ hơn hoặc lớn hơn khoảng 1000 lần: lỗi đơn vị (nghìn ghi thành `50.0`, hoặc cột tính
  bằng nghìn đồng). So với `don_gia * so_luong` trên cùng các dòng.
- Hai bảng cùng cột và tên gần giống nhau mà chưa được gộp (tên cột khác nhau): `UNION ALL` chúng,
  và bảo đảm một dòng không xuất hiện ở cả hai (đếm mã đơn khác nhau ở mỗi bảng).
- Nhiều dòng có NULL ở cột mã đơn hoặc ngày trong khi các cột dòng hàng có giá trị: một bản xuất
  theo nhóm chưa được điền. Điền xuống trong SQL bằng `last_value(col IGNORE NULLS) OVER (ORDER BY
  rowid)` theo thứ tự tệp, hoặc bằng pandas `ffill`.
- Thành tiền dòng so với tổng đơn: đừng cộng tổng cấp đơn một lần cho mỗi dòng. Dùng một dòng mỗi
  đơn (`DISTINCT` theo mã đơn) cho các cột cấp đơn.
- Cùng một mặt hàng viết khác nhau (dấu, hoa thường, khoảng trắng thừa, viết tắt): khớp theo mã khi có;
  nếu không, so sánh văn bản đã fold: `replace(strip_accents(lower(trim(x))), 'đ', 'd')`
  (`strip_accents` giữ nguyên `đ`).
- Ngày: so `min`/`max` của cột ngày với as-of date; các dòng sau đó vẫn tồn tại và phải bị loại. Cột
  ngày còn ở dạng `VARCHAR`: phân tích trong SQL bằng `try_strptime(col, ['%d/%m/%Y', '%Y-%m-%d', ...])`
  hoặc trong pandas (`pd.to_datetime(..., dayfirst=True)`); không bao giờ coi câu hỏi là
  unanswerable chỉ vì ngày cần phân tích.
