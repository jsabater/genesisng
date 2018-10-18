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
curl -v -g "http://127.0.0.1:11223/genesisng/logins/list?page=2&size=50"; echo ""

# List using page, size, sort_by, order_by and fields
curl -v -g "http://127.0.0.1:11223/genesisng/logins/list?page=1&size=50&sort_by=name&order_by=desc&fields=id&fields=name"; echo ""

# List using page, size, sort_by, order_by, fields and filters
curl -v -g "http://127.0.0.1:11223/genesisng/logins/list?page=4&size=40&sort_by=name&order_by=desc&fields=id&fields=name&filters=id|gt|50"; echo ""

# List using page, size, sort_by, order_by and search
curl -v -g "http://127.0.0.1:11223/genesisng/logins/list?page=1&size=50&sort_by=name&order_by=desc&search=Black"; echo ""

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

# List
curl -v -g "http://127.0.0.1:11223/genesisng/guests/list"; echo ""

# List using page and size
curl -v -g "http://127.0.0.1:11223/genesisng/guests/list?page=3&size=35"; echo ""

# List using page, size, sort_by, order_by and fields
curl -v -g "http://127.0.0.1:11223/genesisng/guests/list?page=10&size=20&sort_by=surname&order_by=asc&fields=id&fields=name&fields=surname"; echo ""

# List using page, size, sort_by, order_by, fields and filters
curl -v -g "http://127.0.0.1:11223/genesisng/guests/list?page=10&size=10&sort_by=name&order_by=desc&fields=id&fields=name&fields=surname&fields=email&filters=birthdate|gte|1990-01-01"; echo ""

# List using page, size, sort_by, order_by and search
curl -v -g "http://127.0.0.1:11223/genesisng/guests/list?page=4&size=10&sort_by=country&order_by=asc&search=Palma"; echo ""

# Bookings from a guest
curl -v -g "http://127.0.0.1:11223/genesisng/guests/1/bookings"; echo ""
