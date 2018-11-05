Feature: Login update

Scenario: REST login update

    Given address "@address"
    Given URL path "/@{app}/logins/4/update"
    Given HTTP method "POST"
    Given format "JSON"
    Given request "login-update-mjordan.json"

    When the URL is invoked

    Then response is equal to that from "login-update.json"
    And status is "200"
    And context is cleaned up

Scenario: REST login update on non-existent login

    Given address "@address"
    Given URL path "/@{app}/logins/0/update"
    Given HTTP method "POST"
    Given format "JSON"
    Given request "login-update-mjordan.json"

    When the URL is invoked

    Then status is "404"
    And context is cleaned up

Scenario: REST login update on conflicting e-mail

    Given address "@address"
    Given URL path "/@{app}/logins/1/update"
    Given HTTP method "POST"
    Given format "JSON"
    Given request "login-update-jsabater.json"

    When the URL is invoked

    Then status is "409"

