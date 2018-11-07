Feature: Login listing

Scenario: REST login listing with no parameters

    Given address "@address"
    Given URL path "/@{app}/@{path_login_list}"
    Given HTTP method "GET"
    Given format "JSON"

    When the URL is invoked

    Then status is "200"

