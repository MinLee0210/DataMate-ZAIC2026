---
name: time-expressions
description: Cách các biểu thức thời gian tương đối trong tiếng Việt được đổi thành khoảng ngày. Dùng mỗi khi câu hỏi nhắc đến một kỳ thời gian.
---

# Biểu thức thời gian

Biểu thức thời gian đã được xác định sẵn, một cách tất định, theo `as_of_date`; các khoảng ngày được
đưa kèm mỗi câu hỏi ở mục "Thời gian đã được xác định". Dùng đúng như vậy, gồm cả hai đầu mút:
`WHERE d BETWEEN DATE 'start' AND DATE 'end'`. Không dùng `current_date` hay `now()`.

Rulebook §2, từng dòng:

1. **Dòng có ngày sau `as_of_date` chưa xảy ra.** Một tệp có thể chứa dòng ghi ngày sau `as_of_date`;
   loại chúng khỏi mọi phép đếm, tổng và số dư bằng `d <= as_of_date`. Ngoại lệ: trạng thái hủy/trả
   của một đơn được đọc đúng như ghi, kể cả khi ngày của trạng thái đó sau `as_of_date`; rulebook §1
   vẫn quyết định đơn đó có tính vào doanh thu hay không.
2. **Ngày X, hôm nay, hôm qua** chỉ hỏi hoạt động trong đúng ngày đó.
3. **Từ X đến Y, nhóm X–Y** gồm cả X và Y.
4. **N ngày gần nhất** là N ngày liên tiếp kết thúc vào hôm nay, gồm cả hôm nay.
5. **Quá N, hơn N, trên N, dưới N** không gồm N (`> N`, `< N`). **Từ N trở lên** gồm N (`>= N`).
6. **Tuần** bắt đầu từ thứ Hai. **Tuần này** là từ thứ Hai của tuần này đến hết hôm nay; **tuần trước,
   tuần rồi** là cả tuần thứ Hai–Chủ nhật trước đó.
7. **Tháng M/Y** là cả tháng, từ ngày 1 đến ngày cuối tháng. **Quý Q** là ba tháng dương lịch bắt đầu
   từ tháng 3Q−2.
8. **Tháng này, quý này, năm nay** chạy từ đầu kỳ đến **hết hôm nay**, không bao giờ đến cuối kỳ.
   **Từ đầu năm, từ đầu năm tới nay** là 01/01 năm nay đến hôm nay.
9. **Tháng M, quý Q không có năm** dùng năm nay nếu kỳ đó không bắt đầu sau hôm nay, nếu không thì
   dùng năm ngoái.
10. **Tháng này so với tháng trước**: tháng trước dùng **cùng số ngày**, từ ngày 1 đến cùng số ngày
    như hôm nay, tối đa đến ngày cuối của tháng trước.
11. **Đến hết ngày X, tính đến hôm nay** hỏi về số dư (công nợ, tồn kho, tiền mặt): trạng thái vào
    cuối ngày X, cộng mọi biến động từ đầu dữ liệu đến hết ngày X. Đây không phải kỳ "tháng này".
    Khi câu hỏi như vậy nói "hôm nay", khoảng ngày đã xác định nghĩa là "đến hôm nay", không phải
    bộ lọc trong đúng một ngày.
12. **Tết năm Y, dịp Tết, mùa Tết** là khoảng dương lịch từ **23 tháng Chạp** của năm âm lịch Y−1 đến
    **hết ngày 10 tháng Giêng** của năm âm lịch Y. Không nêu năm thì dùng năm của `as_of_date`.
    **Trước Tết** là cùng số ngày ngay trước 23 tháng Chạp; **N ngày trước Tết** là N ngày ngay trước
    đó. Đọc các ngày này từ `calendar.csv` của bộ dữ liệu, được nạp lúc ingest thành bảng
    `lunar_calendar` (`date`, `lunar_day`, `lunar_month`, `lunar_year`), không bao giờ gõ cứng ngày.
13. **Ca sáng** là 06:00–13:59 và **ca chiều** là 14:00–21:59, theo thời điểm tạo đơn. Khi câu hỏi so
    ca chiều với ca sáng, mốc so sánh là ca sáng.
14. **Không nhắc thời gian**: toàn bộ dữ liệu đến `as_of_date` (`d <= as_of_date`).

Viết tắt hay gặp trong câu hỏi: hnay = hôm nay, hqua = hôm qua, hkia = hôm kia, trc = trước,
thg = tháng.
