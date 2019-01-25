Feature: Login creation and deletion

Scenario: REST login creation with required fields only

    Given address "@address"
    Given URL path "/genesisng/logins/create"
    Given HTTP method "POST"
    Given format "JSON"
    Given request "login-create-lskywalker.json"

    When the URL is invoked

    Then JSON Pointer "/response/id" isn't empty
    And JSON Pointer "/response/username" is "lskywalker"
    And JSON Pointer "/response/name" is "Luke"
    And JSON Pointer "/response/email" is "lskywalker@gmail.com"
    And JSON Pointer "/response/is_admin" is false
    And status is "201"
    And header "Location" isn't empty
    And I store "/response/id" from response under "id"

Scenario: REST login deletion of previously created login

    Given address "@address"
    Given URL path "/genesisng/logins/#{id}/delete"
    Given HTTP method "GET"
    Given format "RAW"
    Given request is "{}"

    When the URL is invoked

    Then status is "204"
    And context is cleaned up

Scenario: REST login creation with all fields and no administrator privileges

    Given address "@address"
    Given URL path "/@{app}/@{path_login_create}"
    Given HTTP method "POST"
    Given format "JSON"
    Given request "login-create-askywalker.json"

    When the URL is invoked

    Then JSON Pointer "/response/id" isn't empty
    And JSON Pointer "/response/username" is "askywalker"
    And JSON Pointer "/response/name" is "Anakin"
    And JSON Pointer "/response/surname" is "Skywalker"
    And JSON Pointer "/response/email" is "askywalker@gmail.com"
    And JSON Pointer "/response/is_admin" is false
    And status is "201"
    And header "Location" isn't empty
    And I store "/response/id" from response under "id"

Scenario: REST login deletion of previously created login

    Given address "@address"
    Given URL path "/@{app}/logins/#{id}/delete"
    Given HTTP method "GET"
    Given format "RAW"
    Given request is "{}"

    When the URL is invoked

    Then status is "204"
    And context is cleaned up

Scenario: REST login creation with all fields and administrator privileges

    Given address "@address"
    Given URL path "/@{app}/@{path_login_create}"
    Given HTTP method "POST"
    Given format "JSON"
    Given request "login-create-bkenobi.json"

    When the URL is invoked

    Then status is "201"
    And JSON Pointer "/response/id" isn't empty
    And JSON Pointer "/response/username" is "bkenobi"
    And JSON Pointer "/response/name" is "Obi-Wan"
    And JSON Pointer "/response/surname" is "Kenobi"
    And JSON Pointer "/response/email" is "bkenobi@gmail.com"
    And JSON Pointer "/response/is_admin" is true
    And header "Location" isn't empty
    And I store "/response/id" from response under "id"

Scenario: REST login deletion of previously created login

    Given address "@address"
    Given URL path "/@{app}/logins/#{id}/delete"
    Given HTTP method "GET"
    Given format "RAW"
    Given request is "{}"

    When the URL is invoked

    Then status is "204"

Scenario: REST login deletion of non-existent login

    Given address "@address"
    Given URL path "/@{app}/logins/#{id}/delete"
    Given HTTP method "GET"
    Given format "RAW"
    Given request is "{}"

    When the URL is invoked

    Then status is "404"
    And context is cleaned up

Scenario: REST login creation of an existing login

    Given address "@address"
    Given URL path "/@{app}/@{path_login_create}"
    Given HTTP method "POST"
    Given format "JSON"
    Given request "login-create-jsabater.json"

    When the URL is invoked

    Then status is "409"

