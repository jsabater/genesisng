#!/bin/bash

# Logins

# Get
curl -v -g "http://127.0.0.1:11223/genesisng/logins/1/get"; echo ""

# Validate
curl -v -g -XPOST -d '{"username": "jsabater", "password": "123456"}' "http://127.0.0.1:11223/genesisng/logins/validate"; echo ""

# Create
curl -v -g -XPOST -d '{"username": "bcamelas", "password": "123456", "name": "Benito", "email": "bcamelas@gmail.com"}' "http://127.0.0.1:11223/genesisng/logins/create"; echo ""

# Delete
curl -v -g "http://127.0.0.1:11223/genesisng/logins/2/delete"; echo ""

# Update
curl -v -g -XPOST -d '{"username": "mjordan", "password": "123456", "name": "Michael", "surname": "Jordan"}' "http://127.0.0.1:11223/genesisng/logins/4/update"; echo ""

# List
curl -v -g "http://127.0.0.1:11223/genesisng/logins/list"; echo ""

# List using page and size
curl -v -g "http://127.0.0.1:11223/genesisng/logins/list?page=2&size=20"; echo ""

# List using page, size and sort
curl -v -g "http://127.0.0.1:11223/genesisng/logins/list?page=2&size=20&sort=name|desc"; echo ""

# List using page, size, sort and fields
curl -v -g "http://127.0.0.1:11223/genesisng/logins/list?page=2&size=20&sort=name|desc&fields=id&fields=name"; echo ""

# List using page, size, sort, fields and filters
curl -v -g "http://127.0.0.1:11223/genesisng/logins/list?page=2&size=20&sort=name|desc&fields=id&fields=name&filters=id|gt|50"; echo ""

# List using sort and multiple filters
curl -v -g "http://127.0.0.1:11223/genesisng/logins/list?sort=name|desc&filters=id|gt|50&filters=id|lt|500&operator=and"; echo ""

# List using sort and search
curl -v -g "http://127.0.0.1:11223/genesisng/logins/list?sort=name|desc&search=Black"; echo ""


# Guests

# Get
curl -v -g "http://127.0.0.1:11223/genesisng/guests/1/get"; echo ""

# Delete
curl -v -g "http://127.0.0.1:11223/genesisng/guests/1/delete"; echo ""

# Restore
curl -v -g "http://127.0.0.1:11223/genesisng/guests/1/restore"; echo ""

# Create
curl -v -g -XPOST -d '{"name": "Michelle", "surname": "Pfeiffer", "gender": "Female", "email": "mpfeiffer@gmail.com", "passport": "12345678A", "birthdate": "1958-04-29", "country": "US", "mobile_phone": "+1.5417543010"}' "http://127.0.0.1:11223/genesisng/guests/create"; echo ""

# Update
curl -v -g -XPOST -d '{"name": "Angelina", "surname": "Jolie", "gender": "Female", "email": "ajolie@gmail.com", "birthdate": "1975-06-04", "address1": "1419 Westwood Blvd", "address2": "Westwood", "locality": "Los Angeles", "postcode": "3H35+W8", "province": "California", "country": "US", "mobile_phone": "+1.5417543010"}' "http://127.0.0.1:11223/genesisng/guests/2/update"; echo ""

# Upsert
curl -v -g -XPOST -d '{"name": "Diane", "surname": "Heidkrüger", "gender": "Female", "email": "dkruger@gmail.com"}' "http://127.0.0.1:11223/genesisng/guests/upsert"; echo ""
curl -v -g -XPOST -d '{"name": "Diane", "surname": "Heidkrüger", "gender": "Female", "email": "dkruger@gmail.com", "birthdate": "1976-07-15", "address1": "St. Matthäus Catholic Church", "address2": "", "locality": "Algermissen", "postcode": "31191", "province": "Lower Saxony", "country": "DE", "mobile_phone": "+49.1511234567"}' "http://127.0.0.1:11223/genesisng/guests/upsert"; echo ""

# List
curl -v -g "http://127.0.0.1:11223/genesisng/guests/list"; echo ""

# List using page and size
curl -v -g "http://127.0.0.1:11223/genesisng/guests/list?page=3&size=35"; echo ""

# List using page, size, sort_by, order_by and fields
curl -v -g "http://127.0.0.1:11223/genesisng/guests/list?page=10&size=20&sort=surname|asc&fields=id&fields=name&fields=surname"; echo ""

# List using page, size, sort_by, order_by, fields and filters
curl -v -g "http://127.0.0.1:11223/genesisng/guests/list?page=10&size=10&sort=name|desc&fields=id&fields=name&fields=surname&fields=email&filters=birthdate|gte|1990-01-01"; echo ""

# List using page, size, sort_by, order_by and search
curl -v -g "http://127.0.0.1:11223/genesisng/guests/list?page=4&size=10&sort=country|asc&search=Palma"; echo ""

# Bookings from a guest
curl -v -g "http://127.0.0.1:11223/genesisng/guests/1/bookings"; echo ""


# Rooms

# Get
curl -v -g "http://127.0.0.1:11223/genesisng/rooms/1/get"; echo ""

# Delete
curl -v -g "http://127.0.0.1:11223/genesisng/rooms/1/delete"; echo ""

# Restore
curl -v -g "http://127.0.0.1:11223/genesisng/rooms/1/restore"; echo ""

# Create
curl -v -g -XPOST -d '{"floor_no": 1, "room_no": 1, "name": "Cosy room with views to the sea", "sgl_beds": 0, "dbl_beds": 1, "supplement": 25}' "http://127.0.0.1:11223/genesisng/rooms/create"; echo ""



# Availability

# Extras
curl -v -g "http://127.0.0.1:11223/genesisng/availability/extras"; echo ""

# Search
curl -v -g "http://127.0.0.1:11223/genesisng/availability/search?guests=3&check_in=2017-07-01&check_out=2017-07-10"; echo ""
curl -v -g "http://127.0.0.1:11223/genesisng/availability/search?guests=3&check_in=2017-07-01&check_out=2017-07-10&rooms=3&rooms=6"; echo ""

# Bookings

curl -v -g -XPOST -d '{"id_guest": 1, "id_room"}' "http://127.0.0.1:11223/genesisng/bookings/create"; echo ""
