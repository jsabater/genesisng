-- Users
INSERT INTO login (username, password, name, surname, email, is_admin)
     VALUES ('admin', 'admin', E'Miguel Ángel', E'Gutiérrez García', 'miguel.gutierrez@ucavila.es ', True),
            ('jsabater', '123456', 'Jaume', 'Sabater', 'jsabater@gmail.com', False)
ON CONFLICT (username, email) DO UPDATE
        SET username = excluded.username,
            password = excluded.password,
            name = excluded.name,
            surname = excluded.surname,
            email = excluded.email,
            is_admin = excluded.is_admin;

-- Guests
INSERT INTO guest (name, surname, gender, email, passport, birthdate, address1, address2, locality, postcode, province, country, home_phone, mobile_phone)
     VALUES ('Isaac', 'Newton', 'Male', 'inewton@genesis.com', '12345678A', '2000-01-01', '221 B Baker St', '', 'London', '07180', 'Greater London', 'GB', '', ''),
            ('Albert', 'Einstein', 'Male', 'aeinstein@genesis.com', '12345678A', '2000-01-01', '221 B Baker St', '', 'London', '07180', 'Greater London', 'GB', '', ''),
            ('Leonardo', 'Pisano Bigollo', 'Male', 'lpisano@genesis.com', '12345678A', '2000-01-01', '221 B Baker St', '', 'London', '07180', 'Greater London', 'GB', '', ''),
            ('Thales', '', 'Male', 'thales@genesis.com', '12345678A', '2000-01-01', '221 B Baker St', '', 'London', '07014', 'Greater London', 'GB', '', ''),
            ('Pythagoras', '', 'Male', 'pythagoras@genesis.com', '12345678A', '2000-01-01', '221 B Baker St', '', 'London', '07014', 'Greater London', 'v', '', ''),
            (E'René', 'Descartes', 'Female', 'rdescartes@genesis.com', '12345678A', '2000-01-01', E'221 B Baker St', '', 'London', '07360', 'Greater London', 'GB', '', ''),
            ('Archimedes', '', 'Male', 'archimedes@genesis.com', '12345678A', '2000-01-01', '221 B Baker St', '', 'London', '07010', 'Greater London', 'GB', '', ''),
            ('John Forbes', 'Nash', 'Male', 'jfnash@genesis.com', '12345678A', '2000-01-01', '221 B Baker St', '', 'London', '07010', 'Greater London', 'GB', '', ''),
            ('Blaise', 'Pascal', 'Male', 'bpascal@genesis.com', '12345678A', '2000-01-01', '221 B Baker St', '', 'London', '07360', 'Greater London', 'GB', '', ''),
            ('Euclid', '', 'Male', 'euclid@genesis.com', '12345678A', '2000-01-01', '221 B Baker St', '', E'London', '07015', 'Greater London', 'v', '', ''),
            ('Aryabhata', '', 'Male', 'aryabhata@genesis.com', '12345678A', '2000-01-01', '221 B Baker St', '', 'London', '07812', 'Greater London', 'GB', '', ''),
            ('Ptolemy', '', 'Male', 'ptolemy@genesis.com', '12345678A', '2000-01-01', '221 B Baker St', '', 'London', '07011', 'Greater London', 'GB', '', ''),
            ('Ada', 'Lovelace', 'Female', 'alovelace@genesis.com', '12345678A', '2000-01-01', '221 B Baker St', '', 'London', '', 'Greater London', 'GB', '', ''),
            ('Alan', 'Turing', 'Male', 'aturing@genesis.com', '12345678A', '2000-01-01', '221 B Baker St', '', 'London', '07007', 'Greater London', 'GB', '', '')
ON CONFLICT (email) DO UPDATE
        SET name = excluded.name,
            surname = excluded.surname,
            gender = excluded.gender,
            email = excluded.email,
            passport = excluded.passport,
            birthdate = excluded.birthdate,
            address1 = excluded.address1,
            address2 = excluded.address2,
            locality = excluded.locality,
            postcode = excluded.postcode,
            province = excluded.province,
            country = excluded.country,
            home_phone = excluded.home_phone,
            mobile_phone = excluded.mobile_phone;

-- Rooms
INSERT INTO room (id, floor_no, room_no, name, sgl_beds, dbl_beds, supplement, code)
     VALUES (1, 1, 1, 'Normal bedroom with two single beds', 2, 0, 20, 'pink'),
            (2, 1, 2, 'Large bedroom with two single and one double beds', 2, 1, 40, 'black'),
            (3, 1, 3, 'Very large bedroom with three single and one double beds', 3, 1, 50, 'white'),
            (4, 1, 4, 'Very large bedroom with four single beds', 4, 0, 40, 'purple'),
            (5, 1, 5, 'Large bedroom with three single beds', 3, 0, 30, 'blue'),
            (6, 1, 6, 'Normal bedroom with one double bed', 0, 1, 20, 'brown')
ON CONFLICT (id) DO UPDATE
        SET floor_no = excluded.floor_no,
            room_no = excluded.room_no,
            name = excluded.name,
            sgl_beds = excluded.sgl_beds,
            dbl_beds = excluded.dbl_beds,
            supplement = excluded.supplement,
            code = excluded.code;

-- Rates
INSERT INTO rate (date_from, date_to, base_price, bed_price, published)
     VALUES ('2017-03-01', '2017-04-30', 10, 20, True),
            ('2017-05-01', '2017-06-30', 20, 30, True),
            ('2017-07-01', '2017-08-31', 30, 40, True),
            ('2017-09-01', '2017-10-31', 20, 30, True)
ON CONFLICT (date_from, date_to) DO UPDATE
        SET date_from = excluded.date_from,
            date_to = excluded.date_to,
            base_price = excluded.base_price,
            bed_price = excluded.bed_price,
            published = excluded.published;

-- Bookings
INSERT INTO booking (id_guest, id_room, reserved, guests, check_in, check_out, checked_in, checked_out, cancelled, base_price, taxes_percentage, taxes_value, total_price, locator, pin, status, meal_plan, additional_services)
     VALUES (1, 1, '2016-12-25 17:00:04', 2, '2017-05-05', '2017-05-09', NULL, NULL, NULL, 200, 10, 20, 220, 'AAAAA', '1234', 'Confirmed', 'BedAndBreakfast', '"PoolKit" => "1"'),
            (2, 2, '2016-12-26 09:03:54', 3, '2017-04-01', '2017-04-11', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAB', '1234', 'Confirmed', 'BedAndBreakfast', '"PoolKit" => "1"'),
            (3, 3, '2016-01-25 14:43:00', 3, '2017-06-02', '2017-06-12', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAC', '1234', 'Confirmed', 'BedAndBreakfast', '"PoolKit" => "1"'),
            (4, 4, '2016-01-25 14:43:00', 3, '2017-06-01', '2017-06-10', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAD', '1234', 'Confirmed', 'BedAndBreakfast', '"PoolKit" => "1"'),
            (5, 5, '2016-01-25 14:43:00', 3, '2017-06-08', '2017-06-18', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAE', '1234', 'Confirmed', 'BedAndBreakfast', '"PoolKit" => "1"'),
            (6, 1, '2016-01-25 14:43:00', 3, '2017-06-11', '2017-06-15', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAF', '1234', 'Confirmed', 'BedAndBreakfast', '"PoolKit" => "1"'),
            (7, 2, '2016-01-25 14:43:00', 2, '2017-05-21', '2017-05-26', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAG', '1234', 'Confirmed', 'BedAndBreakfast', '"PoolKit" => "1"'),
            (8, 3, '2016-01-25 14:43:00', 3, '2017-06-02', '2017-06-16', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAH', '1234', 'Confirmed', 'BedAndBreakfast', '"PoolKit" => "1"'),
            (9, 4, '2016-01-25 14:43:00', 3, '2017-06-11', '2017-06-21', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAI', '1234', 'Confirmed', 'BedAndBreakfast', '"PoolKit" => "1"'),
            (10, 5, '2016-01-25 14:43:00', 3, '2017-06-12', '2017-06-22', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAJ', '1234', 'Confirmed', 'BedAndBreakfast', '"PoolKit" => "1"'),
            (11, 1, '2016-01-25 14:43:00', 1, '2017-06-01', '2017-06-07', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAK', '1234', 'Confirmed', 'BedAndBreakfast', '"PoolKit" => "1"'),
            (12, 2, '2016-01-25 14:43:00', 3, '2017-06-21', '2017-06-29', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAL', '1234', 'Confirmed', 'BedAndBreakfast', '"PoolKit" => "1"'),
            (13, 3, '2016-01-25 14:43:00', 3, '2017-06-19', '2017-06-29', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAM', '1234', 'Confirmed', 'BedAndBreakfast', '"PoolKit" => "1", "LateDinner" => "1"'),
            (1, 4, '2016-01-25 14:43:00', 3, '2017-06-26', '2017-06-07', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAN', '1234', 'Confirmed', 'BedAndBreakfast', '"PoolKit" => "1", "LateDinner" => "1"'),
            (2, 5, '2016-01-25 14:43:00', 3, '2017-08-07', '2017-08-08', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAO', '1234', 'Confirmed', 'BedAndBreakfast', '"PoolKit" => "1", "LateDinner" => "1"'),
            (3, 1, '2016-01-25 14:43:00', 3, '2017-08-03', '2017-08-05', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAP', '1234', 'Confirmed', 'BedAndBreakfast', '"PoolKit" => "1", "LateDinner" => "1"'),
            (4, 2, '2016-01-25 14:43:00', 3, '2017-08-02', '2017-08-12', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAQ', '1234', 'Confirmed', 'BedAndBreakfast', '"PoolKit" => "1", "LateDinner" => "1"'),
            (5, 3, '2016-01-25 14:43:00', 4, '2017-08-01', '2017-08-11', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAR', '1234', 'Confirmed', 'BedAndBreakfast', '"PoolKit" => "1", "LateDinner" => "1"'),
            (6, 4, '2016-01-25 14:43:00', 3, '2017-08-30', '2017-09-05', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAS', '1234', 'Confirmed', 'BedAndBreakfast', '"PoolKit" => "1", "LateDinner" => "1"'),
            (7, 5, '2016-01-25 14:43:00', 3, '2017-08-21', '2017-08-31', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAT', '1234', 'Confirmed', 'BedAndBreakfast', '"PoolKit" => "1", "LateDinner" => "1"'),
            (8, 1, '2016-01-25 14:43:00', 2, '2017-08-11', '2017-08-21', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAU', '1234', 'Confirmed', 'BedAndBreakfast','"Massage" => "1"'),
            (9, 2, '2016-01-25 14:43:00', 2, '2017-06-06', '2017-06-16', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAV', '1234', 'Confirmed', 'BedAndBreakfast','"Massage" => "1"'),
            (10, 3, '2016-01-25 14:43:00', 3, '2017-06-01', '2017-06-10', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAW', '1234', 'Confirmed', 'BedAndBreakfast','"Massage" => "1"'),
            (11, 4, '2016-01-25 14:43:00', 1, '2017-06-01', '2017-06-03', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAX', '1234', 'Confirmed', 'BedAndBreakfast','"Massage" => "1"'),
            (12, 5, '2016-01-25 14:43:00', 3, '2017-05-05', '2017-05-15', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAY', '1234', 'Confirmed', 'BedAndBreakfast','"Massage" => "1"'),
            (13, 1, '2016-01-25 14:43:00', 3, '2017-05-09', '2017-06-19', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAAZ', '1234', 'Confirmed', 'BedAndBreakfast','"Massage" => "1"'),
            (1, 2, '2016-01-25 14:43:00', 2, '2017-05-11', '2017-05-18', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAA1', '1234', 'Confirmed', 'BedAndBreakfast','"Massage" => "1"'),
            (2, 3, '2016-01-25 14:43:00', 2, '2017-05-23', '2017-05-28', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAA2', '1234', 'Confirmed', 'BedAndBreakfast','"Massage" => "1"'),
            (3, 4, '2016-01-25 14:43:00', 2, '2017-07-14', '2017-07-28', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAA3', '1234', 'Confirmed', 'BedAndBreakfast','"Massage" => "1"'),
            (4, 5, '2016-01-25 14:43:00', 3, '2017-07-07', '2017-07-14', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAA4', '1234', 'Confirmed', 'BedAndBreakfast', ''),
            (5, 1, '2016-01-25 14:43:00', 2, '2017-07-01', '2017-07-11', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAA5', '1234', 'Confirmed', 'BedAndBreakfast', ''),
            (6, 2, '2016-01-25 14:43:00', 3, '2017-07-15', '2017-07-30', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAA6', '1234', 'Confirmed', 'BedAndBreakfast', ''),
            (7, 3, '2016-01-25 14:43:00', 2, '2017-06-01', '2017-06-08', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAA7', '1234', 'Confirmed', 'BedAndBreakfast', ''),
            (8, 4, '2016-01-25 14:43:00', 3, '2017-08-08', '2017-08-16', NULL, NULL, NULL, 500, 10, 50, 550, 'AAAA8', '1234', 'Confirmed', 'BedAndBreakfast', '')
ON CONFLICT (id_guest, id_room, check_in) DO UPDATE
        SET id_guest = excluded.id_guest,
            id_room = excluded.id_room,
            reserved = excluded.reserved,
            guests = excluded.guests,
            check_in  = excluded.check_in,
            check_out = excluded.check_out,
            checked_in = excluded.checked_in,
            checked_out = excluded.checked_out,
            cancelled = excluded.cancelled,
            base_price = excluded.base_price,
            taxes_percentage = excluded.taxes_percentage,
            taxes_value = excluded.taxes_value,
            total_price = excluded.total_price,
            locator = excluded.locator,
            pin = excluded.pin;

