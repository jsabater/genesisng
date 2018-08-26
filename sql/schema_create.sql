-- Function that emulates Transact-SQL's IIF (if-and-only-if)
CREATE OR REPLACE FUNCTION IIF(BOOLEAN, DATE, DATE) RETURNS DATE
AS $$
    SELECT CASE $1 WHEN True THEN $2 ELSE $3 END
$$
LANGUAGE SQL IMMUTABLE;

-- Users
CREATE TABLE IF NOT EXISTS login (
    id SERIAL PRIMARY KEY,
    username VARCHAR(20),
    password VARCHAR(255),
    name VARCHAR(50),
    surname VARCHAR(50),
    email VARCHAR(255),
    is_admin BOOLEAN DEFAULT FALSE
);
CREATE UNIQUE INDEX IF NOT EXISTS login_username_email ON login (username, email);

-- Guests
CREATE TYPE Gender AS ENUM ('Male', 'Female');
CREATE TABLE IF NOT EXISTS guest (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    surname VARCHAR(50),
    gender Gender DEFAULT 'Male',
    email VARCHAR(255),
    passport VARCHAR(255),
    birthdate DATE,
    address1 VARCHAR(50),
    address2 VARCHAR(50),
    locality VARCHAR(50),
    postcode VARCHAR(10),
    province VARCHAR(50),
    country VARCHAR(2),
    home_phone VARCHAR(50),
    mobile_phone VARCHAR(50),
    deleted DATE DEFAULT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS guest_email ON guest (email);

-- Rooms
CREATE TABLE IF NOT EXISTS room (
    id SERIAL PRIMARY KEY,
    floor_no INTEGER NOT NULL,
    room_no INTEGER NOT NULL,
    name VARCHAR(100),
    sgl_beds INTEGER DEFAULT 0,
    dbl_beds INTEGER DEFAULT 0,
    accommodates INTEGER NOT NULL,
    supplement REAL DEFAULT 0,
    code VARCHAR(20) UNIQUE NOT NULL,
    deleted DATE DEFAULT NULL,
    CHECK (sgl_beds + dbl_beds > 0)
);
COMMENT ON COLUMN room.code IS 'Unique code used to link to images';

CREATE UNIQUE INDEX IF NOT EXISTS room_floor_no_room_no ON room (floor_no, room_no);
CREATE INDEX IF NOT EXISTS room_name ON room (name);
CREATE INDEX IF NOT EXISTS room_sgl_beds ON room (sgl_beds);
CREATE INDEX IF NOT EXISTS room_dbl_beds ON room (dbl_beds);
CREATE INDEX IF NOT EXISTS room_accommodates ON room (accommodates);

CREATE OR REPLACE FUNCTION room_accommodation()
    RETURNS trigger
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $$
    BEGIN
        NEW.accommodates = NEW.sgl_beds + NEW.dbl_beds * 2;
        RETURN NEW;
   END
   $$;

CREATE TRIGGER room_accommodates
    BEFORE INSERT OR UPDATE
    ON room
    FOR EACH ROW
    EXECUTE PROCEDURE room_accommodation();

-- Rates
CREATE TABLE IF NOT EXISTS rate (
    id SERIAL PRIMARY KEY,
    date_from DATE,
    date_to DATE,
    base_price REAL,
    bed_price REAL,
    published BOOLEAN DEFAULT FALSE,
    CHECK (date_from < date_to),
    -- Prevent dates from overlapping by using an exclusion constraint and the overlap operator (&&) for the daterange type
    EXCLUDE USING GIST (daterange(date_from, date_to) WITH &&)
);
CREATE UNIQUE INDEX IF NOT EXISTS rate_date_from_date_to ON rate (date_from, date_to);

-- Bookings
CREATE TYPE BookingStatus AS ENUM ('New', 'Pending', 'Confirmed', 'Cancelled', 'Closed');
CREATE TYPE BookingMealPlan AS ENUM ('RoomOnly', 'BedAndBreakfast', 'HalfBoard', 'FullBoard', 'AllInclusive', 'Special');
CREATE TABLE IF NOT EXISTS booking (
    id SERIAL PRIMARY KEY,
    id_guest INTEGER REFERENCES guest(id),
    id_room INTEGER REFERENCES room(id),
    reserved TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    nights INTEGER,
    guests INTEGER,
    check_in DATE,
    check_out DATE,
    checked_in TIMESTAMP,
    checked_out TIMESTAMP,
    cancelled TIMESTAMP,
    base_price REAL,
    taxes_percentage REAL,
    taxes_value REAL,
    total_price REAL,
    locator VARCHAR(50),
    pin VARCHAR(50),
    status BookingStatus DEFAULT 'New',
    meal_plan BookingMealPlan DEFAULT 'BedAndBreakfast',
    additional_services HSTORE,
    uuid VARCHAR(255),
    deleted DATE DEFAULT NULL
);

CREATE OR REPLACE FUNCTION booking_nights()
    RETURNS trigger
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $$
    BEGIN
        NEW.nights = date_part('day', age(NEW.check_out::timestamp, NEW.check_in::timestamp));
        RETURN NEW;
   END
   $$;

CREATE TRIGGER booking_nights
    BEFORE INSERT OR UPDATE
    ON booking
    FOR EACH ROW
    EXECUTE PROCEDURE booking_nights();

CREATE UNIQUE INDEX IF NOT EXISTS booking_id_guest_id_room_check_in ON booking (id_guest, id_room, check_in);
CREATE UNIQUE INDEX IF NOT EXISTS booking_locator ON booking (locator);
CREATE INDEX IF NOT EXISTS booking_check_in ON booking(check_in);
CREATE INDEX IF NOT EXISTS booking_check_out ON booking(check_out);

