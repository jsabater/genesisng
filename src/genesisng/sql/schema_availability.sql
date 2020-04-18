-- Function that emulates Transact-SQL's IIF (if-and-only-if)
CREATE OR REPLACE FUNCTION IIF(BOOLEAN, DATE, DATE) RETURNS DATE
AS $$
    SELECT CASE $1 WHEN True THEN $2 ELSE $3 END
$$ LANGUAGE SQL IMMUTABLE;

-- Function to have together all steps that lead to availability and pricing calculation
CREATE OR REPLACE FUNCTION availability_search(check_in DATE, check_out DATE,
    guests INTEGER, rooms INTEGER[] DEFAULT '{}')
    RETURNS TABLE (
        r_id INTEGER,
        r_floor_no INTEGER,
        r_room_no INTEGER,
        r_name VARCHAR,
        r_sgl_beds INTEGER,
        r_dbl_beds INTEGER,
        r_accommodates INTEGER,
        r_code VARCHAR,
        t_nights INTEGER,
        t_price REAL
    ) AS $$
BEGIN
RETURN QUERY
(
    WITH p AS (
         -- Sum of nights and prices per season (0..N)
         SELECT SUM(IIF($2 > t.date_to, t.date_to, $2) - IIF($1 > t.date_from, $1, t.date_from)) AS nights,
                SUM(
                    (IIF($2 > t.date_to, t.date_to, $2) - IIF($1 > t.date_from, $1, t.date_from)) *
                    (t.base_price + t.bed_price * $3)
                ) AS price
           FROM rate AS t
          WHERE (t.date_from, t.date_to) OVERLAPS ($1, $2)
            AND t.published = True
         ),
         a AS (
         -- Room availability
         SELECT r.id AS r_id,
                r.floor_no AS r_floor_no,
                r.room_no AS r_room_no,
                r.name AS r_name,
                r.sgl_beds AS r_sgl_beds,
                r.dbl_beds AS r_dbl_beds,
                (r.sgl_beds + r.dbl_beds * 2) AS r_accommodates,
                r.supplement AS r_supplement,
                r.code AS r_code
           FROM room AS r
          WHERE r.id NOT IN (
                SELECT b.id_room
                  FROM booking as b
                 WHERE (b.check_in, b.check_out) OVERLAPS ($1, $2)
                   AND b.cancelled IS NULL
                )
            AND (r.sgl_beds + r.dbl_beds * 2) >= $3
            AND CASE WHEN $4 = '{}'::INTEGER[] THEN r.id > 0 ELSE r.id = ANY($4) END
         )
  SELECT a.r_id AS r_id,
         a.r_floor_no AS r_floor_no,
         a.r_room_no AS r_room_no,
         a.r_name AS r_name,
         a.r_sgl_beds AS r_sgl_beds,
         a.r_dbl_beds AS r_dbl_beds,
         a.r_accommodates AS r_accommodates,
         a.r_code AS r_code,
         p.nights::INTEGER AS t_nights,
         (a.r_supplement * p.nights + p.price)::REAL AS t_price
    FROM a, p
ORDER BY t_price ASC, r_accommodates ASC, r_sgl_beds ASC, r_dbl_beds ASC, r_floor_no ASC, r_room_no ASC
);
END
$$ LANGUAGE plpgsql;
