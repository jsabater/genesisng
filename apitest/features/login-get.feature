Feature: Login details

Scenario: REST login details

    Given address "@address"
    Given URL path "/genesisng/logins/1/get"
    # Given I store "@default_login_id" under "id"
    # Given URL path "/@app/@path_login_get"
    Given HTTP method "GET"
    Given format "JSON"

    When the URL is invoked

    Then response is equal to that from "login-get.json"
    And status is "200"
