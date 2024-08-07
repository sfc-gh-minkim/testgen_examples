# Example 1: SNOW-1492382

## Original PR Information

**URL:** https://github.com/snowflakedb/snowflake/pull/189910

**JIRA:** SNOW-1492382 Migrated `application_package_security_review_dropping.py` to Snowfort.

## Migration Details

### Original Files
* **SFTest File:** [t_native_apps_provider_platform_trust/src/application_package_security_review_dropping.py](https://github.com/snowflakedb/snowflake/blob/219948a7c9b65283a323139cea89a3cabdf5b259/RegressionTests/regressions/t_native_apps_provider_platform_trust/src/application_package_security_review_dropping.py)

* **SFTest Ref File:** 
[t_native_apps_provider_platform_trust/ref/application_package_security_review_dropping.py.ref](https://github.com/snowflakedb/snowflake/blob/6bf9883fd94688c462c87997b3129caaf2e5578b/RegressionTests/regressions/t_native_apps_provider_platform_trust/ref/application_package_security_review_dropping.py.ref)

### Changelog
- Migrated `application_package_security_review_dropping.py` to Snowfort
- Changed `application_package_security_review_api`

## LLM Test generation Details
We use a modified SWEAgent to generate the test. In the current version we copy the Snowflake repo into the docker in which SWEAgent can freely interact with the terminal. However it's unable to execute the actual tests at the moment.



## LLM Generated Files
- [GENERATED_test_application_package_security_review_max.py][data/outputs/GENERATED_test_application_package_security_review_max.py]
- [GOLD_test_application_package_security_review_max.py][data/outputs/GOLD_test_application_package_security_review_max.py]
- c
- ...

## Notes
[Add any additional notes, concerns, or follow-up items here]