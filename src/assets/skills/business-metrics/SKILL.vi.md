---
name: business-metrics
description: Công thức SQL cho các thuật ngữ nghiệp vụ của rulebook (đơn hợp lệ, doanh thu, số đơn, đơn vị, trung bình, tỉ trọng, tăng trưởng, khách hàng, công nợ). Dùng cho mọi câu hỏi về tiền, số lượng, đơn hàng hoặc khách hàng.
---

# Chỉ số kinh doanh

Rulebook (cuối prompt này) định nghĩa từng thuật ngữ; làm theo nó, và theo phần của loại hình cửa
hàng khi có. Dưới đây là cách tính chúng trên các bảng bạn nhận được.

## Macro hỗ trợ (có trong mọi cơ sở dữ liệu cửa hàng)
- `is_cancelled(status)`, `is_returned(status)`: true với mọi cách viết trạng thái
  (`hủy đơn`, `Đã hủy đơn`, `Huỷ đơn`, `khách hủy`; `hàng trả về`, `Đổi trả`, `Đã hoàn hàng`).
  **Dùng chúng thay vì so sánh với một cách viết**: một cửa hàng thường viết cùng một trạng thái
  theo 2-4 cách, và `= 'Đã hủy'` bỏ sót các cách còn lại (số đơn hủy bằng 0 hầu như luôn là lỗi này).
  Cả hai trả về false với trạng thái trống hoặc NULL; vì vậy `NOT is_cancelled(status) AND NOT
  is_returned(status)` giữ lại các dòng bình thường không ghi trạng thái.
- `is_walk_in(customer_name)`: `khách lẻ`, `Khách lẻ`, `kl`, `lẻ`, `vãng lai`, để trống. Đơn khách lẻ
  không bao giờ là một khách hàng trong phép đếm hay xếp hạng.
- `fold(x)`: chữ thường, bỏ dấu, `đ` → `d`; dùng để so sánh tên và nhãn.

## View đã sinh sẵn (dùng khi prompt có liệt kê)
Ingest dựng các view này từ chính cột của shop; mục "Semantic views available" trong prompt cho
biết view nào có và đúng tên cột. Ưu tiên dùng chúng thay vì suy lại rulebook:
- `v_sales` — mỗi dòng hàng một dòng (hoặc mỗi đơn khi shop không có bảng chi tiết). `is_valid`
  đã loại đơn huỷ và đơn có dòng trả hàng; `is_walk_in` đánh dấu dòng không phải khách;
  `sale_date` là ngày **đặt**; `line_total` là tiền dòng sau giảm giá dòng, không trừ giảm giá
  cấp đơn, không VAT, không phí giao; `base_quantity` đã quy về đơn vị cơ bản khi shop có ghi.
  `order_paid` chỉ có khi bảng là đầu đơn: không cộng nó trên các dòng.
- `v_orders` — mỗi đơn một dòng: `order_date`, `is_valid`, `is_walk_in`, `customer_code`,
  `customer_name`, `order_total` (tổng tiền dòng của đơn). Đếm đơn và tính trung bình một đơn ở
  đây, không ở `v_sales`.
- `v_products` — mã/tên hàng, `base_unit`, `big_unit`, hệ số `factor`, `cost_price`, `category`.
  Chỉ nhân số lượng với `factor` khi `base_quantity` trống.
- `v_stock` — số tồn shop ghi, theo mặt hàng.
- `v_purchases` — phiếu nhập theo `purchase_date`, kèm nhà cung cấp và số tiền.
View không có nghĩa là cột của shop không đủ: quay lại dùng các bảng.
`v_sales` có mọi dòng shop ghi, kể cả dòng không phải mặt hàng (phí phục vụ, voucher, điểm, phí
ship). Giữ hay bỏ các dòng đó theo `item_name` đúng như rulebook nói.

## Đơn hợp lệ
- Hợp lệ = `NOT is_cancelled(status) AND NOT is_returned(status)`. Mọi trạng thái khác (xong,
  `Thành công`, đang giao) đều hợp lệ.
- Đơn có **bất kỳ** dòng nào bị trả là đơn trả: loại cả đơn, không chỉ dòng đó. Dựng trước tập mã đơn,
  rồi lọc các dòng bằng `order_code NOT IN (...)`.
- Khi cột trạng thái chỉ nằm ở bảng đơn, nối các dòng với đơn theo mã đơn.
- Khi trạng thái nằm trong cột ghi chú (không có cột trạng thái), đọc từ đó; ghi chú không nhắc
  trạng thái nghĩa là đơn đã hoàn thành.

## Doanh thu (doanh thu, tiền hàng, bán được bao nhiêu tiền)
- Tổng **thành tiền của dòng hàng sau giảm giá dòng** của các đơn hợp lệ, theo **ngày đặt đơn**.
- Không phải tổng đơn sau giảm giá đơn hay voucher, không VAT, không phí ship, không phải số tiền
  đã thanh toán. Nếu chỉ có `số lượng * đơn giá` và giảm giá dòng, dùng
  `số lượng * đơn giá - giảm giá dòng`.
- Bảng có cả tiền cấp đơn và cấp dòng: không bao giờ cộng tổng đơn một lần cho mỗi dòng.
- Dòng "Phí phục vụ" tính vào doanh thu, nhưng không phải là một mặt hàng trong xếp hạng hay đếm.

## Đếm và số lượng
- Số đơn: `count(DISTINCT order_code)` trên các đơn hợp lệ.
- Số lượng theo đơn vị cơ sở: nhân với hệ số quy đổi (bảng hoặc cột "quy đổi"; đơn vị không có dòng
  quy đổi có hệ số 1). Dùng cột đơn vị cơ sở có sẵn khi có.
- "Bán được bao nhiêu <đơn vị>": chỉ các mặt hàng có **đơn vị cơ sở** là đơn vị đó, đã quy đổi.

## Đơn vị và giá
- Giá hoặc giá vốn "theo <đơn vị>" (một hộp, một viên, một thùng) là theo **đúng** đơn vị đó: quy đổi
  bằng bảng quy đổi. Giá nhập trung bình = sum(số lượng × giá) / sum(số lượng), theo đơn vị được
  hỏi, không phải tổng các giá và không theo đơn vị cơ sở khi câu hỏi nêu đơn vị lớn hơn.
- "Số bill", "số đơn", "số phiếu" là số chứng từ, không phải tiền.

## Trung bình, tỉ trọng, tăng trưởng
- Trung bình tiền làm tròn đến đồng, làm tròn lên khi .5: `round(CAST(x AS DECIMAL(18,4)), 0)`,
  không bao giờ `round(x, 2)` (giá trị đơn hàng trung bình là tiền).
- Các trung bình và phần trăm khác: 2 chữ số thập phân. Phần trăm tính theo điểm: `100.0 * part / total`.
- Tỉ trọng của một nhóm chia cho doanh thu của **cả cửa hàng** trong cùng kỳ (đơn khách lẻ nằm
  trong mẫu số).
- Tăng trưởng: `100.0 * (hiện tại - trước) / trước`, âm khi giảm. Chênh lệch số tiền:
  `hiện tại - so sánh`, cùng đơn vị.
- Tỉ lệ hủy: số đơn hủy / **tất cả** đơn đặt trong kỳ (mọi trạng thái).
- Phần trăm tính theo điểm: 66.01 chứ không phải 0.6601; tỉ trọng là phần trăm, không bao giờ là số tiền.
- "X tăng hay giảm bao nhiêu % so với Y": X là kỳ hiện tại, Y là kỳ gốc; đáp án là
  `100.0 * (X - Y) / Y`. Tính X và Y với cùng bộ lọc (đơn hợp lệ, cùng định nghĩa doanh thu), rồi
  kiểm tra dấu so với hai con số trước khi trả lời.
- Tác động của việc đổi giá ("tăng giá từ A lên B ngày D … N ngày kể từ đó so với N ngày trước"):
  trả lời được từ các dòng đơn hàng. Sau = ngày D đến D+N-1, trước = ngày D-N đến D-1, cùng mặt hàng,
  đơn hợp lệ; đáp án là phần trăm thay đổi `100.0 * (sau - trước) / trước` của số lượng (hoặc
  doanh thu, nếu được hỏi). Đừng trả lời unanswerable chỉ vì không có bảng lịch sử giá: câu hỏi đã
  cho sẵn ngày.
- Số đơn theo trạng thái ("đơn huỷ", "đơn trả hàng"): dùng macro `is_cancelled` / `is_returned` trên
  cột trạng thái, không bao giờ so khớp chuỗi chính xác. Số đếm bằng 0 trong một kỳ có đơn nghĩa là
  bộ lọc bỏ sót: hãy xem các giá trị trạng thái khác nhau trước.

## Khách hàng
- Có mã khách: một mã = một khách; đơn không có mã (khách lẻ) không phải một khách hàng. Không có
  mã: khách hàng là tên trên đơn, các tên chỉ khác nhau cách viết (hoa thường, dấu, khoảng trắng) là
  cùng một khách; "Khách lẻ" không phải khách hàng.

## Công nợ
- Công nợ của một đơn tại ngày X: tổng đơn (sau giảm giá đơn, gồm phí ship) trừ các khoản thanh
  toán đến hết ngày X. Loại đơn hủy; đơn trả vẫn tính. Đơn COD và đơn sàn không phải công nợ.
- Tuổi nợ: số ngày từ **ngày đặt đơn** đến hôm nay (đơn đặt hôm nay là 0 ngày).
- Thu nợ ("thu nợ", "tiền khách trả nợ", "thu hồi công nợ") trong một kỳ: các khoản thanh toán có
  **ngày thanh toán** nằm trong kỳ, trên các đơn ghi nợ, trừ khoản thanh toán lúc mua (cùng ngày với
  đơn, hoặc dòng thanh toán loại thanh toán đầu). Lọc theo ngày thanh toán, không phải ngày đặt
  đơn: khoản nợ trả tháng 6 cho đơn tháng 5 tính vào tháng 6.
