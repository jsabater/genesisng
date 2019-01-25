Feature: Login details

Scenario: REST login details

    Given address "@address"
    Given URL path "/genesisng/logins/1/get"
    Given HTTP method "GET"
    Given format "JSON"

    When the URL is invoked

    Then response is equal to that from "login-get.json"
    And status is "200"
