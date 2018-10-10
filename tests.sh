#!/bin/bash

# Logins
curl -v -g "http://127.0.0.1:11223/genesisng/logins/1/get"; echo ""
curl -v -g -XPOST -d '{"username": "jsabater", "password": "123456"}' "http://127.0.0.1:11223/genesisng/logins/validate"; echo ""
curl -v -g -XPOST -d '{"username": "bcamelas", "password": "123456", "name": "Benito", "email": "bcamelas@gmail.com"}' "http://127.0.0.1:11223/genesisng/logins/create"; echo ""
curl -v -g "http://127.0.0.1:11223/genesisng/logins/2/delete"; echo ""
curl -v -g -XPOST -d '{"username": "mjordan", "password": "123456", "name": "Michael", "surname": "Jordan"}' "http://127.0.0.1:11223/genesisng/logins/4/update"; echo ""
curl -v -g "http://127.0.0.1:11223/genesisng/logins/list"; echo ""
curl -v -g "http://127.0.0.1:11223/genesisng/logins/list?page=1&size=50"; echo ""
curl -v -g "http://127.0.0.1:11223/genesisng/logins/list?page=1&size=50&sort_by=name&order_by=desc&fields=id&fields=name"; echo ""
curl -v -g "http://127.0.0.1:11223/genesisng/logins/list?page=1&size=50&sort_by=name&order_by=desc&fields=id&fields=name&filters=id|gt|50"; echo ""
curl -v -g "http://127.0.0.1:11223/genesisng/logins/list?page=1&size=50&sort_by=name&order_by=desc&search=Black"; echo ""

# Guests
curl -v -g "http://127.0.0.1:11223/genesisng/guests/1/get"; echo ""
