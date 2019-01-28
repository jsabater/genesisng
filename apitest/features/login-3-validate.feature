Feature: Login validation

Scenario: REST login successful validation

    Given address "@address"
    Given URL path "/@{app}/logins/validate"
    Given HTTP method "POST"
    Given format "JSON"
    Given request "login-validate-jsabater.json"

    When the URL is invoked

    Then status is "200"
    And response is equal to that from "login-get-jsabater.json"
    And context is cleaned up

Scenario: REST login unsuccessful validation

    Given address "@address"
    Given URL path "/@{app}/logins/validate"
    Given HTTP method "POST"
    Given format "JSON"
    Given request "login-validate-yoda.json"

    When the URL is invoked

    Then status is "403"

