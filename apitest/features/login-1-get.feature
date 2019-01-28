Feature: Login details

Scenario: REST login details

    Given address "@address"
    Given URL path "/@{app}/logins/1/get"
    Given HTTP method "GET"
    Given format "JSON"

    When the URL is invoked

    Then status is "200"
    And response is equal to that from "login-get-jsabater.json"

