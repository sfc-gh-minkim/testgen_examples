import pytest
from snowfort.testlib.annotations.features import FeatureArea
from snowfort.testlib.annotations.isolation import SFIsolationLevel
from snowfort.testlib.annotations.runtime import Runtime
from snowfort.testlib.annotations.sut import SUT
from snowfort.testlib.base_test import BaseTest
from snowfort.testlib.native_apps.annotations.accounts import NativeAppsMultipleAccounts, NativeAppsProviderAccount
from snowfort.testlib.native_apps.api.application_package_api import ApplicationPackageProperty
from snowfort.testlib.native_apps.api.native_apps_api import NativeAppsApi
from snowfort.testlib.native_apps.api.native_apps_sql import NativeAppsSql
from snowfort.testlib.native_apps.api.stage_api import StageEncryption
from snowfort.testlib.native_apps.constants.database_flag import DatabaseFlag
from snowfort.testlib.native_apps.constants.distribution import Distribution
from snowfort.testlib.native_apps.constants.parameters import Parameter
from snowfort.testlib.native_apps.fixtures.security_scanner import SecurityScanner
from snowfort.testlib.native_apps.models.application import Application
from snowfort.testlib.native_apps.models.application_package import ApplicationPackage
from snowfort.testlib.native_apps.models.application_package_security_review import ReviewState
from snowfort.testlib.native_apps.templates.setup_script import SetupScript

@SecurityScanner
@FeatureArea.native_apps
@SUT.local_fs
@Runtime.precommit
@NativeAppsMultipleAccounts.with_args(
    provider=NativeAppsMultipleAccounts.CreationSettings(
        {
            Parameter.ENABLE_NATIVE_APPS_BG_VERSION_DROPPER: True,
            Parameter.DISABLE_NATIVE_APPS_BG_UPGRADE_FOR_TEST: True,
            Parameter.ENABLE_NATIVE_APPLICATION_TRUST_INTEGRATION: True,
            Parameter.ENABLE_APPLICATION_PACKAGE_VERSION_AUTOMATED_SECURITY_REVIEW: True,
            Parameter.ENABLE_APPLICATION_PACKAGE_VERSION_TRUST_ENFORCEMENT: True,
        }
    ),
    scanner=NativeAppsMultipleAccounts.CreationSettings(
        parameters={Parameter.ENABLE_SECURITY_REVIEW_SYSTEM_FUNCS: True},
    ),
)
class TestApplicationPackageSecurityReviewMax(BaseTest):
    """Migrated from application_package_security_review_max.py"""
@pytest.fixture(scope="function")
def _app_package(self, api: NativeAppsApi, sql: NativeAppsSql) -> ApplicationPackage:
    api.procedure.call("SYSTEM$INTERNAL_NATIVE_APPS_BG_UPGRADE_CTRL", args=["sync"])
    api.procedure.call("SYSTEM$CLEANUP_APPLICATION_SECURITY_REVIEWS_IN_REQUESTER", use_snowflake_connection=True)
    api.listing.accept_provider_monetization_terms()
    api.global_metadata.sync_full()

    stage = api.stage.create(encryption_type=StageEncryption.SNOWFLAKE_FULL)
    api.stage.prepare_app_stage(stage)

    app_package = api.application_package.create()
    api.application_package.add_version(app_package, stage=stage)
    api.application_package.add_patch(app_package, stage=stage)
    api.application_package.add_patch(app_package, stage=stage)
    api.application_package.add_patch(app_package, stage=stage)
    api.application_package.add_patch(app_package, stage=stage)
    api.application_package.alter_set(app_package, {ApplicationPackageProperty.DISTRIBUTION: Distribution.EXTERNAL})
    api.global_metadata.sync_full()
    return app_package
def test_security_review(self, api: NativeAppsApi, _app_package: ApplicationPackage):
    app = api.application.create(app_package=_app_package)
    api.application_package.set_security_review_state(
        app_package=_app_package, expected_state=ReviewState.PASSED
    )
    api.application_package.assert_latest_patch_security_review_state(
        app_package=_app_package, expected_state=ReviewState.PASSED
    )
    api.global_metadata.sync_full()
    assert app.security_review_state == ReviewState.PASSED

