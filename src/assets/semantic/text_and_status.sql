-- Generic helpers for messy text, from rulebook §1, §3 and §8. Every business gets them.
-- fold: lowercase, accents off, đ -> d, trimmed ('Huỷ đơn' and 'hủy đơn' both give 'huy don').
CREATE OR REPLACE MACRO fold(x) AS replace(strip_accents(lower(trim(CAST(x AS VARCHAR)))), 'đ', 'd');

-- Cancelled order, however the status is written: hủy / Huỷ đơn / Đã hủy / khách hủy / cancelled.
CREATE OR REPLACE MACRO is_cancelled(status) AS
    fold(status) LIKE '%huy%' OR fold(status) LIKE '%cancel%';

-- Returned order: trả hàng / hàng trả về / Đổi trả / Đã hoàn hàng / Hoàn trả / returned.
-- Not 'hoàn thành' (completed): only 'hoan hang' and 'hoan tra' count.
CREATE OR REPLACE MACRO is_returned(status) AS
    fold(status) LIKE '%tra hang%' OR fold(status) LIKE '%tra ve%' OR fold(status) LIKE '%doi tra%'
    OR fold(status) LIKE '%hoan hang%' OR fold(status) LIKE '%hoan tra%' OR fold(status) LIKE '%return%';

-- Walk-in customer (khách lẻ, kl, lẻ, vãng lai, empty): not a customer for counts and rankings.
CREATE OR REPLACE MACRO is_walk_in(name) AS
    name IS NULL OR fold(name) IN ('', 'khach le', 'kl', 'le', 'khachle', 'khach vang lai', 'vang lai', 'khach', 'walk in', 'walk-in');
