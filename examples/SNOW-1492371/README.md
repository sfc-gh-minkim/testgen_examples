# Example 1: SNOW-1492371

## Original PR Information

**URL:** https://github.com/snowflakedb/snowflake/pull/190531/

**JIRA:** SNOW-1492371 

Migrated `application_package_security_review_max.py` to Snowfort.

## Migration Details

### Original Files
* **SFTest File:** 

[t_native_apps_provider_platform_trust/src/application_package_security_review_max.py](https://github.com/snowflakedb/snowflake/blob/92390ec1ca5543200294b914b3205a269658f140/RegressionTests/regressions/t_native_apps_provider_platform_trust/src/application_package_security_review_max.py)

* **SFTest Ref File:** 

[t_native_apps_provider_platform_trust/ref/application_package_security_review_max.py.ref](https://github.com/snowflakedb/snowflake/blob/92390ec1ca5543200294b914b3205a269658f140/RegressionTests/regressions/t_native_apps_provider_platform_trust/ref/application_package_security_review_max.py.ref)

### Changelog
- Migrated `application_package_security_review_max.py` to Snowfort

## LLM Test generation Details
### Model/LLM
We use a modified SWEAgent using gpt4o to generate the test. In the current version we copy the Snowflake repo into the docker in which SWEAgent can freely interact with the terminal. However it's unable to execute the actual tests at the moment.

Besides standard SWEAgent prompts, we use the following task instruction:
```
JIRA: SNOW-1492371
Migrate application_package_security_review_max.py to Snowfort.

Here are the original SFTest Files:

RegressionTests/regressions/t_native_apps_provider_platform_trust/src/application_package_security_review_max.py.
Original SFTest Ref File:

t_native_apps_provider_platform_trust/ref/application_package_security_review_max.py.ref

Migrate them to Snowfort.
```

### State of repo
Since we couldn't find the repo state before the PR, we used the up-to-date main branch for now, but manually reset the `application_package_security_review_max.py` file by emptying out its contents.

We also manually add `RegressionTests/regressions/t_native_apps_provider_platform_trust/src/application_package_security_review_max.py`.

### LLM Inputs
- We provide a direct hint in the agent prompt:
```
2. To understand Snowfort syntax and framework, you can explore and study existing examples of written tests,
   for example : Snowfort/tests/native_apps/provider_platform/trust/test_application_package_security_review_dropping.py
```
- This referenced file can be found at:
[test_application_package_security_review_dropping.py](https://github.com/snowflakedb/snowflake/blob/46acb94d6d30568ccad78e1cce28ff0d2c6de2a8/Snowfort/tests/native_apps/provider_platform/trust/test_application_package_security_review_dropping.py)


## LLM Generated Files
- LLM Generated file: 

[GENERATED_test_application_package_security_review_max.py](https://github.com/sfc-gh-minkim/testgen_examples/blob/main/examples/SNOW-1492382/data/outputs/GENERATED_test_application_package_security_review_max.py)

- Gold Generated file:

[GOLD_test_application_package_security_review_max.py](https://github.com/sfc-gh-minkim/testgen_examples/blob/main/examples/SNOW-1492382/data/outputs/GOLD_test_application_package_security_review_max.py)

## Notes
[Add any additional notes, concerns, or follow-up items here]